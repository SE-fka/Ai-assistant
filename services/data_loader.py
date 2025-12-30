import asyncio
import logging
import time
from pathlib import Path
from tqdm import tqdm
from config.settings import settings
from services.file_processor import file_processor
from services.embedding_service import embedding_service
from db.database import db
from typing import List, Dict, Any

class DataLoader:
    def __init__(self, data_path: str = settings.DATA_PATH):
        self.data_path = Path(data_path)
        self.processed_files = set()
        self.failed_files = {}

        try:
            self.data_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"📁 DataLoader initialized with path: {self.data_path}")
        except Exception as e:
            logging.error(f"❌ Failed to create data directory {self.data_path}: {e}")
            raise

    async def load_existing_files(self) -> bool:
        try:
            existing_docs = db.get_all_documents()
            if existing_docs is None:
                logging.warning("⚠️ Database returned None for existing documents")
                self.processed_files = set()
                return False

            self.processed_files = {doc["filename"] for doc in existing_docs if "filename" in doc}
            logging.info(f"📁 Loaded {len(self.processed_files)} processed files from database")
            return True

        except Exception as e:
            logging.error(f"❌ Error loading existing files from database: {e}")
            self.processed_files = set()
            return False

    def discover_files(self) -> List[Path]:
        try:
            if not self.data_path.exists() or not self.data_path.is_dir():
                logging.error(f"❌ Data path does not exist or is not a directory: {self.data_path}")
                return []

            files = []
            supported_extensions = file_processor.get_supported_formats()

            for ext in supported_extensions:
                pattern = f"*{ext}" if ext.startswith(".") else f"*.{ext}"
                found_files = list(self.data_path.rglob(pattern))
                files.extend(found_files)

            valid_files = [
                f for f in files
                if f.is_file() and f.exists() and not file_processor.is_temporary_file(f.name)
            ]

            new_files = [
                f for f in valid_files
                if f.name not in self.processed_files and f.name not in self.failed_files
            ]

            logging.info(f"🎯 Found {len(valid_files)} total valid files, {len(new_files)} new files to process")
            return new_files

        except Exception as e:
            logging.error(f"❌ Error discovering files: {e}")
            return []

    async def process_single_file(self, file_path: Path) -> Dict[str, Any]:
        try:
            logging.info(f"🔄 Processing: {file_path.name}")

            if file_processor.is_temporary_file(file_path.name):
                error_msg = f"Temporary file skipped: {file_path.name}"
                logging.info(f"🔒 {error_msg}")
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "skipped"}

            if not file_path.exists() or not file_path.is_file():
                error_msg = f"Invalid file: {file_path}"
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "failed"}

            file_size = file_path.stat().st_size
            if file_size == 0:
                error_msg = "File is empty"
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "failed"}

            document_data = await file_processor.process_file(str(file_path), file_path.name)
            if not document_data or not document_data.get("processing_success", False):
                error_msg = "File processing error or no content extracted"
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "failed"}

            chunks = await embedding_service.chunk_and_embed(document_data["content"], {"filename": file_path.name})
            if not chunks:
                error_msg = "No chunks created from content"
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "failed"}

            document_data.update({
                "chunks": chunks,
                "chunk_count": len(chunks),
                "file_path": str(file_path),
                "upload_date": time.time(),
                "file_size": file_size
            })

            document_id = db.insert_document(document_data)
            if not document_id:
                error_msg = "Failed to insert document into database"
                self.failed_files[file_path.name] = error_msg
                return {"filename": file_path.name, "error": error_msg, "status": "failed"}

            self.processed_files.add(file_path.name)
            self.failed_files.pop(file_path.name, None)
            logging.info(f"✅ Successfully processed: {file_path.name} -> {len(chunks)} chunks")

            return {
                "filename": file_path.name,
                "document_id": document_id,
                "chunks_created": len(chunks),
                "status": "success"
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logging.error(f"❌ Unexpected error processing {file_path.name}: {e}", exc_info=True)
            self.failed_files[file_path.name] = error_msg
            return {"filename": file_path.name, "error": error_msg, "status": "failed"}

    async def process_all_files(self, batch_size: int = settings.BATCH_SIZE) -> Dict[str, Any]:
        try:
            await self.load_existing_files()
            files = self.discover_files()

            if not files:
                logging.info("ℹ️ No new files to process")
                return {
                    "message": "No new files to process",
                    "processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "total_files": 0,
                    "status": "no_files"
                }

            logging.info(f"🚀 Starting to process {len(files)} files with batch size {batch_size}")
            results = {
                "total_files": len(files),
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [],
                "successful_files": [],
                "failed_files": {},
                "skipped_files": []
            }

            semaphore = asyncio.Semaphore(batch_size)

            async def process_with_semaphore(file_path):
                async with semaphore:
                    return await self.process_single_file(file_path)

            tasks = [process_with_semaphore(file_path) for file_path in files]

            with tqdm(total=len(files), desc="📂 Processing files") as pbar:
                for i in range(0, len(tasks), batch_size):
                    batch_tasks = tasks[i:i + batch_size]
                    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                    for result in batch_results:
                        if isinstance(result, Exception):
                            results["failed"] += 1
                            results["errors"].append(f"Task exception: {str(result)}")
                        else:
                            results["processed"] += 1
                            if result.get("status") == "success":
                                results["successful"] += 1
                                results["successful_files"].append(result["filename"])
                            elif result.get("status") == "skipped":
                                results["skipped"] += 1
                                results["skipped_files"].append(result["filename"])
                            else:
                                results["failed"] += 1
                                results["failed_files"][result['filename']] = result.get('error', 'Unknown error')

                        pbar.update(1)

            self._log_processing_summary(results)
            return results

        except Exception as e:
            logging.error(f"💥 Critical error in process_all_files: {e}", exc_info=True)
            return {
                "total_files": 0,
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "errors": [f"Critical error: {str(e)}"],
                "status": "critical_error"
            }

    def _log_processing_summary(self, results: Dict[str, Any]):
        total = results["total_files"]
        successful = results["successful"]
        failed = results["failed"]
        skipped = results["skipped"]

        if failed > 0 or skipped > 0:
            logging.warning(f"⚠️ Processing complete: {successful}/{total} successful, {failed} failed, {skipped} skipped")
            for error in results["errors"][:3]:
                logging.warning(f"   - {error}")
            if len(results["errors"]) > 3:
                logging.warning(f"   ... and {len(results['errors']) - 3} more errors")
        else:
            logging.info(f"🎉 Processing complete: {successful} files processed successfully")

    def get_processing_stats(self) -> Dict[str, Any]:
        try:
            return {
                "data_path": str(self.data_path),
                "processed_files_count": len(self.processed_files),
                "failed_files_count": len(self.failed_files),
                "data_directory_exists": self.data_path.exists(),
                "supported_formats": file_processor.get_supported_formats(),
                "temporary_file_patterns": file_processor.get_temporary_file_patterns()
            }
        except Exception as e:
            logging.error(f"Error getting processing stats: {e}")
            return {
                "data_path": str(self.data_path),
                "error": str(e)
            }

    def clear_failed_files(self):
        self.failed_files.clear()
        logging.info("🧹 Cleared failed files cache")

    async def retry_failed_files(self) -> Dict[str, Any]:
        if not self.failed_files:
            return {
                "message": "No failed files to retry",
                "processed": 0,
                "successful": 0,
                "failed": 0
            }

        logging.info(f"🔄 Retrying {len(self.failed_files)} failed files")
        files_to_retry = [self.data_path / filename for filename in self.failed_files.keys()]
        failed_files_backup = self.failed_files.copy()
        self.failed_files.clear()

        results = await self.process_all_files()

        for filename in failed_files_backup.keys():
            if filename in results.get("failed_files", {}):
                self.failed_files[filename] = results["failed_files"][filename]

        return results

data_loader = DataLoader()

async def process_data_directory(data_path: str = None, batch_size: int = None) -> Dict[str, Any]:
    try:
        loader = DataLoader(data_path) if data_path else data_loader
        if batch_size is None:
            batch_size = getattr(settings, 'BATCH_SIZE', 5)

        return await loader.process_all_files(batch_size)

    except Exception as e:
        logging.error(f"❌ Error in process_data_directory: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }

async def main():
    try:
        results = await process_data_directory()
        print(f"Processing results: {results}")
    except Exception as e:
        logging.error(f"Example usage failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())