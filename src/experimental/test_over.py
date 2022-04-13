import os
import sys
import uuid

if __name__ == "__main__":
    print("ARGV:", sys.argv)
    print("EXEC:", sys.executable)
    print("PID:", os.getpid())

    id = uuid.uuid4()
    print("ID:", id)
