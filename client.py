import sys
import os
import grpc
import time
import yaml
import threading
import logging
import ast
from concurrent import futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | Client | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('client.log', mode='a')
    ]
)

# Add project directory to sys.path
project_dir = os.path.abspath(os.path.dirname(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
    logging.info(f"client.py: Added {project_dir} to sys.path")

try:
    import fileService_pb2
    import fileService_pb2_grpc
    import heartbeat_pb2
    import heartbeat_pb2_grpc
    import fluffy_pb2
    import fluffy_pb2_grpc
except ImportError as e:
    logging.error(f"Import error in client.py: {e}")
    raise

def getFileChunks():
    CHUNK_SIZE = 4000000  # 4MB chunks
    username = input("Enter Username: ")
    filename = input("Enter filename: ")
    if not username or not filename:
        logging.error("Username or filename is empty")
        raise ValueError("Username and filename cannot be empty")
    outfile = os.path.join('files', filename)
    logging.info(f"Attempting to open file: {outfile}")
    
    if not os.path.exists(outfile):
        logging.error(f"File {outfile} not found")
        raise FileNotFoundError(f"File {outfile} not found")
    
    if os.path.getsize(outfile) == 0:
        logging.error(f"File {outfile} is empty")
        raise ValueError(f"File {outfile} is empty")
    
    try:
        with open(outfile, 'rb') as infile:
            logging.info("File opened successfully")
            sTime = time.time()
            seq_no = 0
            while True:
                chunk = infile.read(CHUNK_SIZE)
                if not chunk:
                    break
                logging.info(f"Sending chunk: username={username}, filename={filename}, seqNo={seq_no}, size={len(chunk)}")
                yield fileService_pb2.FileData(
                    username=username,
                    filename=filename,
                    data=chunk,
                    seqNo=seq_no
                )
                seq_no += 1
            if seq_no == 0:
                logging.warning(f"No chunks sent for {outfile}")
                raise ValueError("No data to send")
            logging.info(f"Chunking completed: time={time.time() - sTime:.2f}s, chunks={seq_no}")
    except Exception as e:
        logging.error(f"Error reading file {outfile}: {type(e).__name__}: {e}")
        raise

def downloadTheFile(stub):
    username = input("Enter Username: ")
    filename = input("Enter file name: ")
    if not username or not filename:
        logging.error("Username or filename is empty")
        print("Username and filename cannot be empty")
        return
    data = bytes("", 'utf-8')
    sTime = time.time()
    try:
        logging.info(f"Downloading file: username={username}, filename={filename}")
        responses = stub.DownloadFile(fileService_pb2.FileInfo(username=username, filename=filename))
        for response in responses:
            logging.info(f"Received chunk: seqNo={response.seqNo}, size={len(response.data)}")
            data += response.data
        logging.info(f"Download completed: time={time.time() - sTime:.2f}s, total_size={len(data)}")
        filePath = os.path.join('downloads', filename)
        os.makedirs('downloads', exist_ok=True)
        with open(filePath, 'wb') as saveFile:
            saveFile.write(data)
        print(f"File Downloaded - {filename}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during download: {e.details()}, code={e.code()}")
        print(f"Download failed: {e.details()}")

def uploadTheFileChunks(stub):
    try:
        logging.info("Starting file upload")
        response = stub.UploadFile(getFileChunks())
        if response.success:
            logging.info("Upload successful")
            print("File successfully Uploaded")
        else:
            logging.error(f"Upload failed: {response.message}")
            print(f"Failed to upload. Message - {response.message}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during upload: {e.details()}, code={e.code()}")
        print(f"Upload failed: {e.details()}")
    except Exception as e:
        logging.error(f"Upload error: {type(e).__name__}: {e}")
        print(f"Upload failed: {str(e)}")

def deleteTheFile(stub):
    username = input("Enter Username: ")
    filename = input("Enter file name: ")
    if not username or not filename:
        logging.error("Username or filename is empty")
        print("Username and filename cannot be empty")
        return
    confirm = input(f"Are you sure you want to delete '{filename}' for '{username}'? (y/n): ")
    if confirm.lower() != 'y':
        logging.info("Deletion cancelled")
        print("Deletion cancelled.")
        return
    try:
        logging.info(f"Deleting file: username={username}, filename={filename}")
        response = stub.FileDelete(fileService_pb2.FileInfo(username=username, filename=filename))
        if response.success:
            logging.info("Delete successful")
            print(f"File '{filename}' successfully deleted for user '{username}'.")
        else:
            logging.error(f"Delete failed: {response.message}")
            print(f"Failed to delete file '{filename}': {response.message}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during delete: {e.details()}, code={e.code()}")
        print(f"Delete failed: {e.details()}")

def isFilePresent(stub):
    username = input("Enter Username: ")
    filename = input("Enter file name: ")
    if not username or not filename:
        logging.error("Username or filename is empty")
        print("Username and filename cannot be empty")
        return
    try:
        logging.info(f"Checking file existence: username={username}, filename={filename}")
        response = stub.FileSearch(fileService_pb2.FileInfo(username=username, filename=filename))
        logging.info(f"FileSearch result: success={response.success}, message={response.message}")
        if response.success:
            print(f"File '{filename}' exists for user '{username}'.")
        else:
            print(f"File '{filename}' does not exist for user '{username}': {response.message}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during FileSearch: {e.details()}, code={e.code()}")
        print(f"File search failed: {e.details()}")

def updateFile(stub):
    try:
        logging.info("Starting file update")
        response = stub.UpdateFile(getFileChunks())
        if response.success:
            logging.info("Update successful")
            print("File successfully updated")
        else:
            logging.error(f"Update failed: {response.message}")
            print(f"Failed to update the file: {response.message}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during update: {e.details()}, code={e.code()}")
        print(f"Update failed: {e.details()}")
    except Exception as e:
        logging.error(f"Update error: {type(e).__name__}: {e}")
        print(f"Update failed: {str(e)}")

def sendFileInChunks(username, filename, seq):
    CHUNK_SIZE = 4000000  # 4MB chunks
    if not username or not filename:
        logging.error("Username or filename is empty")
        raise ValueError("Username and filename cannot be empty")
    outfile = os.path.join('files', filename)
    logging.info(f"Sending file multiple times: username={username}_{seq}, filename={filename}")
    
    if not os.path.exists(outfile):
        logging.error(f"File {outfile} not found")
        raise FileNotFoundError(f"File {outfile} not found")
    
    if os.path.getsize(outfile) == 0:
        logging.error(f"File {outfile} is empty")
        raise ValueError(f"File {outfile} is empty")
    
    try:
        with open(outfile, 'rb') as infile:
            seq_no = 0
            while True:
                chunk = infile.read(CHUNK_SIZE)
                if not chunk:
                    break
                logging.info(f"Sending chunk: username={username}_{seq}, filename={filename}, seqNo={seq_no}, size={len(chunk)}")
                yield fileService_pb2.FileData(
                    username=f"{username}_{seq}",
                    filename=filename,
                    data=chunk,
                    seqNo=seq_no
                )
                seq_no += 1
            if seq_no == 0:
                logging.warning(f"No chunks sent for {outfile}")
                raise ValueError("No data to send")
            logging.info(f"Chunking completed for sequence {seq}: chunks={seq_no}")
    except Exception as e:
        logging.error(f"Error sending file {outfile} for sequence {seq}: {type(e).__name__}: {e}")
        raise

def sendFileMultipleTimes(stub):
    username = input("Enter Username: ")
    filename = input("Enter file name: ")
    if not username or not filename:
        logging.error("Username or filename is empty")
        print("Username and filename cannot be empty")
        return
    
    try:
        numberOfTimes = int(input("How many times you want to send this file? "))
        if numberOfTimes <= 0:
            logging.error("Number of uploads must be positive")
            print("Please enter a positive number.")
            return
        if numberOfTimes > 100:
            logging.warning("Large number of uploads requested")
            confirm = input(f"Are you sure you want to upload the file {numberOfTimes} times? (y/n): ")
            if confirm.lower() != 'y':
                logging.info("Multiple uploads cancelled")
                print("Operation cancelled.")
                return
    except ValueError:
        logging.error("Invalid input for number of times")
        print("Please enter a valid number.")
        return
    
    success_count = 0
    for i in range(1, numberOfTimes + 1):
        try:
            logging.info(f"Uploading file iteration {i} for username={username}_{i}")
            response = stub.UploadFile(sendFileInChunks(username, filename, i))
            logging.info(f"Upload result for iteration {i}: success={response.success}, message={response.message}")
            if response.success:
                print(f"File successfully uploaded for username '{username}_{i}' (iteration {i})")
                success_count += 1
            else:
                print(f"Failed to upload for username '{username}_{i}' (iteration {i}): {response.message}")
        except grpc.RpcError as e:
            logging.error(f"gRPC error during upload {i}: {e.details()}, code={e.code()}")
            print(f"Upload failed for username '{username}_{i}' (iteration {i}): {e.details()}")
        except Exception as e:
            logging.error(f"Upload error for iteration {i}: {type(e).__name__}: {e}")
            print(f"Upload failed for username '{username}_{i}' (iteration {i}): {str(e)}")
    
    print(f"\nUpload Summary: {success_count}/{numberOfTimes} uploads successful")

def getListOfAllTheFilesForTheUser(stub):
    username = input("Enter Username: ")
    if not username:
        logging.error("Username is empty")
        print("Username cannot be empty")
        return
    try:
        logging.info(f"Listing files for username={username}")
        response = stub.FileList(fileService_pb2.UserInfo(username=username))
        logging.info(f"File list received: {response.Filenames}")
        if response.Filenames:
            try:
                file_list = ast.literal_eval(response.Filenames) if response.Filenames else []
                if file_list:
                    print(f"Files for {username}:")
                    for idx, filename in enumerate(file_list, 1):
                        print(f"  {idx}. {filename}")
                else:
                    print(f"No files found for user '{username}'.")
            except (ValueError, SyntaxError) as e:
                logging.error(f"Failed to parse file list: {response.Filenames}, error={str(e)}")
                print(f"Error parsing file list: {str(e)}")
        else:
            print(f"No files found for user '{username}'.")
    except grpc.RpcError as e:
        logging.error(f"gRPC error during file list: {e.details()}, code={e.code()}")
        print(f"File list failed: {e.details()}")

def handleUserInputs(stub):
    while True:
        print("===================================")
        print("1. Upload a file")
        print("2. Download a file")
        print("3. Delete a file")
        print("4. Check if a file is present")
        print("5. Update a file")
        print("6. Get a list of all the files for a user")
        print("7. Send a file multiple times")
        print("===================================")
        option = input("Please choose an option: ")
        logging.info(f"User selected option: {option}")
        if option == '1':
            uploadTheFileChunks(stub)
        elif option == '2':
            downloadTheFile(stub)
        elif option == '3':
            deleteTheFile(stub)
        elif option == '4':
            isFilePresent(stub)
        elif option == '5':
            updateFile(stub)
        elif option == '6':
            getListOfAllTheFilesForTheUser(stub)
        elif option == '7':
            sendFileMultipleTimes(stub)
        else:
            logging.warning("Invalid option selected")
            print("Invalid option. Please try again.")

def run_client(serverAddress):
    with grpc.insecure_channel(serverAddress) as channel:
        try:
            grpc.channel_ready_future(channel).result(timeout=1)
            logging.info(f"Connected to {serverAddress}")
            print("Connected")
        except grpc.FutureTimeoutError:
            logging.error("Connection timeout")
            print("Connection timeout. Unable to connect to port")
            return
        stub = fileService_pb2_grpc.FileserviceStub(channel)
        handleUserInputs(stub)

if __name__ == '__main__':
    run_client('localhost:9000')