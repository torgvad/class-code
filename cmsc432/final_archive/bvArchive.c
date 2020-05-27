#include<stdio.h>
#include<stdlib.h>
#include<sys/types.h>
#include<sys/dir.h>
#include<dirent.h>
#include<fcntl.h>
#include<unistd.h>
#include<string.h>
#include <errno.h>
#include <sys/stat.h>

//Find the location off where the file offset is located and return it
unsigned long long int ReadFile(int fID) {
	unsigned long long int fileLen;
	read(fID, (void*)&fileLen, sizeof(unsigned long long int));
	unsigned long long int fileOffset = 0;
	unsigned long long int offset_loc = lseek(fID, 0, SEEK_CUR);
	read(fID, (void*)&fileOffset, 8);
	int nameLen;
	read(fID, (void*)&nameLen, sizeof(nameLen));
	char name[nameLen];
	read(fID, (void*)&name, nameLen);
	return (offset_loc);

}

//Go through the folder's data to move the cursor to the next file
void ReadFolder(int fID) {
	int start_loc = lseek(fID, 0, SEEK_CUR);
	int fileCount;
	read(fID, (void*)&fileCount, sizeof(fileCount));
	int nameLen;
	read(fID, (void*)&nameLen, sizeof(nameLen));
	char name[nameLen];
	read(fID, (void*)&name, nameLen);
}

//Read up until it hits a file. Then return the file's offset location
unsigned long long int FileReader(int fID, unsigned long long int end) {
	while (lseek(fID, 0, SEEK_CUR) != end) {
		int loc = lseek(fID, 0, SEEK_CUR);
		char isFolder;
		read(fID, (void*)&isFolder, sizeof(isFolder));
		if (isFolder == 1) {
			ReadFolder(fID);
		}
		else {
			return(ReadFile(fID));
		}
	}
	return (1);
}

//Go through the parent directory and recursively go through all the files and subdirectories
int directory_explorer(char directory[], int fID, int writingID, unsigned long long int offset, char * name) {
	struct dirent * de;
	DIR *dir = opendir(directory);
	int isDir = 1;
	//Check if path leads to a directory or a file
	if (dir == NULL) {
		isDir = 0;
	}
	int fileCount = 0;
	int folderCount = 0;
	//If it is a directory go through its contents and call directory_explorer on each one
	if (isDir == 1) {
		int num = 1;
		char flag = 1;
		write(writingID, (void*)&flag, sizeof(flag));
		strcat(directory, "/");
		int isDir = 0;
		int howFarOffset = 8 + strlen(name) + 1;
		while ((de = readdir(dir)) != NULL) {
			if (strcmp(de->d_name, ".") != 0 && strcmp(de->d_name, "..") != 0) {
				fileCount += 1;
				char backup[strlen(de->d_name)];
				strcpy(backup, de->d_name);
				char ah[strlen(directory) + strlen(de->d_name) + 1];
				strcpy(ah, directory);
				strcat(ah, de->d_name);
				char * ay = de->d_name;
				//If the file called is a directory then it will return how far this folder has to "jump forward" to go past that folder's content
				isDir = directory_explorer(ah, fID, writingID, offset + howFarOffset, de->d_name);
				if (isDir == 0) {
					howFarOffset += 21;
					howFarOffset += strlen(de->d_name);
				}
				else {
					howFarOffset += isDir;
				}
			}
		}
		//Go back and write the metadata for this directory
		//Directory metada consists of a 1 byte flag to indicate its a folder, an int for file count, an int for name length, and the name
		lseek(writingID, offset, SEEK_SET);
		char isFile = 1;
		write(writingID, (void*)&isFile, sizeof(isFile));
		write(writingID, (void*)&fileCount, sizeof(fileCount));
		int size = strlen(name);
		write(writingID, (void*)&size, sizeof(size));
		for (int j = 0; j != strlen(name); j++) {
			write(writingID, (void*)&name[j], 1);
		}
		int loc = lseek(writingID, 0, SEEK_CUR);
		return (howFarOffset);
	}
	//If its a file then write its data at the offset. Nothing is returned as the function that called this one will know what the new offset will be
	else {
		//File metadata consists of a 1 byte flag to indicate its a file, unsigned long long for the file size, unsigned long long for the offset to find the data inside the archive, int name lenght, and name
		lseek(writingID, offset, SEEK_SET);
		int currFile = open(directory, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
		unsigned long long int size = lseek(currFile, 0, SEEK_END);
		unsigned long long int offset = 0;
		char isFile = 0;
		write(writingID, (void*)&isFile, sizeof(isFile));
		write(writingID, (void*)&size, sizeof(size));
		write(writingID, (void*)&offset, 8);
		int namesize = strlen(name);
		write(writingID, (void*)&namesize, sizeof(namesize));

		for (int j = 0; j != strlen(name); j++) {
			write(writingID, (void*)&name[j], 1);
		}
		int loc = lseek(writingID, 0, SEEK_CUR);
		return(0);
	}
	closedir(dir);
}

int findFileinSystem(char directory[], char wantedFile[]) {
	struct dirent * de;
	DIR *dir = opendir(directory);
	if (dir == NULL) {
		closedir(dir);
		return 0;
	}
	strcat(directory, "/");
	while ((de = readdir(dir)) != NULL) {
		int return_int = 0;
		if (strcmp(de->d_name, ".") != 0 && strcmp(de->d_name, "..") != 0) {
			char next_dir[strlen(directory) + strlen(de->d_name)];
			strcpy(next_dir, directory);
			strcat(next_dir, de->d_name);
			if (strcmp(de->d_name, wantedFile) == 0) {
				int currFile = open(strcat(directory, wantedFile), O_RDWR, S_IRUSR | S_IWUSR);
				return (currFile);
			}
			return_int = findFileinSystem(next_dir, wantedFile);
			if (return_int != 0) {
				return (return_int);
			}
		}
	}
}

int main(int argc, char** argv) {
	char * partitionName = argv[1];
	char * archive = argv[2];

	int fID = open(partitionName, O_CREAT | O_RDWR | O_EXCL, 0644);
	if (fID < 0) {
		if (errno == EEXIST) {
			fID = open(partitionName, O_CREAT | O_RDWR, S_IRUSR | S_IWUSR);
		}
		else {
			printf("Something went wrong");
		}

	}

	int writingID = open(archive, O_CREAT | O_RDWR | O_EXCL, 0644);
	if (writingID < 0) {
		if (errno == EEXIST) {
			writingID = open(archive, O_TRUNC | O_RDWR, S_IRUSR | S_IWUSR);
		}
		else {
			printf("Something went wrong");
		}
	}

	//Go through the directory and write its metadata to file
	directory_explorer(partitionName, fID, writingID, 0, partitionName);

	//Go to the start of the file and add the actual file data along with changing the metadata's offset to the file data
	unsigned long long int ending = lseek(writingID, 0, SEEK_END);
	unsigned long long int offset = 0;
	unsigned long long int something = lseek(writingID, 0, SEEK_END);
	lseek(writingID, 0, SEEK_SET);
	while (offset != 1) {
		//File reader will return 1 when all the metadata has been read through
		offset = FileReader(writingID, ending);
		if (offset == 1) {
			break;
		}
		int start_loc = lseek(writingID, 0, SEEK_CUR);
		something = lseek(writingID, 0, SEEK_END);
		lseek(writingID, offset, SEEK_SET);
		write(writingID, (void*)&something, sizeof(something));
		int nameLen;
		read(writingID, (void*)&nameLen, sizeof(nameLen));
		char fileName[nameLen];
		char actualName[nameLen];
		read(writingID, (void*)&fileName, nameLen);
		for (int i = 0; i < nameLen; i++) {
			actualName[i] = fileName[i];
		}
		for (int i = 0; i <= nameLen; i++) {
			if (i == nameLen) {
				actualName[i] = '\0';
			}
		}
		char dirName[strlen(argv[1])];
		int size = strlen(argv[1]);
		strncpy(dirName, argv[1], size - 1);
		//Go through the directories to find the current file by name
		int fileID = findFileinSystem(dirName, actualName);
		lseek(writingID, 0, SEEK_END);
		unsigned long long int file_ending;
		//Go to the end of the archive file and transfer the file's data one byte at a time
		file_ending = lseek(fileID, 0, SEEK_END);
		lseek(fileID, 0, SEEK_SET);
		char byte;
		while (lseek(fileID, 0, SEEK_CUR) < file_ending) {
			read(fileID, (void*)&byte, 1);
			write(writingID, (void*)&byte, sizeof(byte));
		}
		lseek(writingID, start_loc, SEEK_SET);
	}
	return (0);
}