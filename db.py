import redis
import ast
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | DB | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('node.log', mode='a')
    ]
)

class DB:
    def __init__(self):
        try:
            self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
            self.client.ping()
            logging.info("Connected to Redis")
        except redis.ConnectionError as e:
            logging.error(f"Redis connection failed: {e}")
            raise

    def setData(self, key, value):
        try:
            if isinstance(value, bytes):
                success = self.client.set(key, value)
            else:
                success = self.client.set(key, str(value).encode('utf-8'))
            logging.info(f"setData: key={key}, value_type={type(value)}, success={success}")
            return success
        except Exception as e:
            logging.error(f"setData error: key={key}, {type(e).__name__}: {e}")
            return False

    def getData(self, key):
        try:
            value = self.client.get(key)
            logging.info(f"getData: key={key}, value_type={type(value)}")
            return value
        except Exception as e:
            logging.error(f"getData error: key={key}, {type(e).__name__}: {e}")
            return None

    def getFileData(self, key):
        # Added for compatibility with DownloadHelper.py
        try:
            value = self.client.get(key)
            logging.info(f"getFileData: key={key}, value_type={type(value)}")
            return value if value else bytes("", 'utf-8')
        except Exception as e:
            logging.error(f"getFileData error: key={key}, {type(e).__name__}: {e}")
            return bytes("", 'utf-8')

    def deleteEntry(self, key):
        try:
            success = self.client.delete(key)
            logging.info(f"deleteEntry: key={key}, deleted={success}")
            return success
        except Exception as e:
            logging.error(f"deleteEntry error: key={key}, {type(e).__name__}: {e}")
            return False

    def saveUserFile(self, username, filename):
        try:
            key = f"{username}"
            current_files = self.client.get(key)
            file_list = ast.literal_eval(current_files.decode('utf-8')) if current_files else []
            if filename not in file_list:
                file_list.append(filename)
                success = self.client.set(key, str(file_list).encode('utf-8'))
                logging.info(f"saveUserFile: username={username}, filename={filename}, file_list={file_list}, success={success}")
                return success
            logging.info(f"saveUserFile: filename={filename} already in {username}'s file_list")
            return True
        except Exception as e:
            logging.error(f"saveUserFile error: username={username}, filename={filename}, {type(e).__name__}: {e}")
            return False

    def getUserFiles(self, username):
        try:
            key = f"{username}"
            files = self.client.get(key)
            file_list = files.decode('utf-8') if files else str([])
            logging.info(f"getUserFiles: username={username}, files={file_list}")
            return file_list
        except Exception as e:
            logging.error(f"getUserFiles error: username={username}, {type(e).__name__}: {e}")
            return str([])

    def saveMetaData(self, username, filename, primary_node, replica_node):
        try:
            key = f"{username}_{filename}"
            meta_data = [primary_node, replica_node]
            success = self.client.set(key, str(meta_data).encode('utf-8'))
            logging.info(f"saveMetaData: key={key}, meta_data={meta_data}, success={success}")
            return success
        except Exception as e:
            logging.error(f"saveMetaData error: key={key}, {type(e).__name__}: {e}")
            return False

    def parseMetaData(self, username, filename):
        try:
            key = f"{username}_{filename}"
            meta_data = self.client.get(key)
            if meta_data:
                parsed = ast.literal_eval(meta_data.decode('utf-8'))
                logging.info(f"parseMetaData: key={key}, meta_data={parsed}")
                return parsed
            logging.warning(f"parseMetaData: No metadata found for key={key}")
            return None
        except Exception as e:
            logging.error(f"parseMetaData error: key={key}, {type(e).__name__}: {e}")
            return None

    def keyExists(self, key):
        try:
            exists = self.client.exists(key)
            logging.info(f"keyExists: key={key}, exists={exists}")
            return exists > 0
        except Exception as e:
            logging.error(f"keyExists error: key={key}, {type(e).__name__}: {e}")
            return False