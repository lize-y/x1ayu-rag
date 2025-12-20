from enum import Enum

class IngestOp(Enum):
    ADDED = "added"
    UPDATED = "updated"
    SKIPPED = "skipped"
    DELETED = "deleted"
    ERROR = "errors"
    BATCH_RESULT = "batch_result"
