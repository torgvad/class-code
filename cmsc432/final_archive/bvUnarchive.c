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


void unarchive(int readingID, char path[], int fileCount) {
	int dirMake = mkdir(path, 0700);
	//Based on the folder's fileCount loop that many times
	for (int i = 0; i < fileCount; i++) {
		char isFolder;
		read(readingID, (void*)&isFolder, sizeof(isFolder));
		//If the file is a directory read its data, construct a path and call unarchive()
		if (isFolder == 1) {
			int fileC;
			read(readingID, (void*)&fileC, sizeof(fileC));
			int nameLen;
			read(readingID, (void*)&nameLen, sizeof(nameLen));
			char name[nameLen];
			read(readingID, (void*)&name, nameLen);
			for (int i = 0; i <= nameLen; i++) {
				if (i == nameLen) {
					name[i] = '\0';
				}
			}
			char partitionName[strlen(path) + 1 + strlen(name)];
			strcpy(partitionName, path);
			strcat(partitionName, "/");
			strcat(partitionName, name);
			unarchive(readingID, partitionName, fileC);
		}
		//If the file isn't a directory then read its data then find the name, create the path, and write the data
		else {
			unsigned long long int fileLen;
			read(readingID, (void*)&fileLen, sizeof(unsigned long long int));
			unsigned long long int fileOffset = 0;
			unsigned long long int offset_loc = lseek(readingID, 0, SEEK_CUR);
			read(readingID, (void*)&fileOffset, 8);
			int nameLen;
			read(readingID, (void*)&nameLen, sizeof(nameLen));
			char name[nameLen];
			read(readingID, (void*)&name, nameLen);
			for (int i = 0; i <= nameLen; i++) {
				if (i == nameLen) {
					name[i] = '\0';
				}
			}
			char partitionName[strlen(path) + 1 + strlen(name)];
			strcpy(partitionName, path);
			strcat(partitionName, "/");
			strcat(partitionName, name);
			//Create the file in the right path then transfer the data from the archive byte at a time
			int fID = open(partitionName, O_CREAT | O_RDWR | O_EXCL, 0644);
			int loc = lseek(readingID, 0, SEEK_CUR);
			unsigned long long start = lseek(readingID, fileOffset, SEEK_SET);
			char byte;
			while (lseek(readingID, 0, SEEK_CUR) != start + fileLen) {
				read(readingID, (void*)&byte, 1);
				write(fID, (void*)&byte, sizeof(byte));
			}
			lseek(readingID, loc, SEEK_SET);

		}
	}
}

int main(int argc, char** argv) {
	int status;
	char archive[strlen(argv[1])];
	strcpy(archive, argv[1]);
	int writingID = open(archive, O_CREAT | O_RDWR | O_EXCL, 0644);
	if (writingID < 0) {
		if (errno == EEXIST) {
			writingID = open(archive, O_RDWR, S_IRUSR | S_IWUSR);
		}
		else {
			printf("Something went wrong");
		}
	}

	//Go to the start of the file and read the parent folder's data
	lseek(writingID, 0, SEEK_SET);
	int start_loc = lseek(writingID, 0, SEEK_CUR);
	char isFolder;
	read(writingID, (void*)&isFolder, sizeof(isFolder));
	int fileCount;
	read(writingID, (void*)&fileCount, sizeof(fileCount));
	int nameLen;
	read(writingID, (void*)&nameLen, sizeof(nameLen));
	char name[nameLen];
	read(writingID, (void*)&name, nameLen);
	for (int i = 0; i <= nameLen; i++) {
		if (i == nameLen) {
			name[i] = '\0';
		}
	}

	char direct[strlen(name)];
	strncpy(direct, name, strlen(name) - 1);

	unarchive(writingID, direct, fileCount);
	return (0);
}