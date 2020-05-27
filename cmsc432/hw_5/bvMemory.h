#include<unistd.h>
#include<stdio.h>
#include<stdlib.h>

int block_num = 0;
void * memory;
int initialized = 0;
long long starting_address;

struct Link {
	long long start;
	long long size;
	struct Link * next;
};

struct Link * head;

int * print_all_links() {
	struct Link * link = head;
	while(link->next != NULL) {
		printf("node: %lld %lld\n", link->start, link->size);
		link = link->next;
	}
		printf("node: %lld %lld\n", link->start, link->size);
}

void * best_fit(struct Link * newLink) {
	int i = 0;
	int hole_sizes[block_num];
	int flag = 0;
	void * result;
	struct Link * smallestTrackerLink;
	struct Link * prevLink;
	struct Link * currentLink = head;
	int location = 0;
	int smallest = 0;
	int first_small = 0;
	//Check if there's a gap in the middle that's the exact size of newLink
	if (currentLink->start == newLink->size) {
		newLink->start = 0;
		newLink->next = currentLink;
		head = newLink;
		block_num++;
		result = memory + newLink->start;
		return memory + newLink->start;
	}
	//Check if there's a gap large enough to accomodate newLink
	if (currentLink->start >= newLink->size) {
		first_small = 1;
	}
	//If the currentLink is the head
	if (currentLink->next == NULL) {
		newLink->start = currentLink->start + currentLink->size;
		currentLink->next = newLink;
		newLink->next = NULL;
		result = memory + newLink->start;
		block_num++;
		return memory + newLink->start;
	}
	//Loop through checking if any gaps are a perfect size. Otherwise the smallest gap and the link before it are stored
	while (currentLink->next != NULL) {
		prevLink = currentLink;
		currentLink = currentLink->next;
		if (currentLink->start - (prevLink->start + prevLink->size) > newLink->size) {
			if (smallest == 0) {
				smallest = currentLink->start - (prevLink->start + prevLink->size);
				smallestTrackerLink = prevLink;
			}
			else {
				if (currentLink->start - (prevLink->start + prevLink->size) < smallest) {
					smallest = currentLink->start - (prevLink->start + prevLink->size);
					smallestTrackerLink = prevLink;
					first_small = 0;
				}
			}
		}
		if (currentLink->start - (prevLink->start + prevLink->size) == newLink->size) {
			newLink->start = prevLink->start + prevLink->size;
			newLink->next = currentLink;
			prevLink->next = newLink;
			result = memory + newLink->start;
			block_num++;
			return memory + newLink->start;
		}
	}
	//If the smallest is the gap before head
	if (first_small == 1) {
		newLink->start = 0;
		newLink->next = head;
		head = newLink;
		return memory + newLink->start;
	}
	//If there's a smallest found
	if (smallest != 0) {
		newLink->start = smallestTrackerLink->start + smallestTrackerLink->size;
		newLink->next = smallestTrackerLink->next;
		smallestTrackerLink->next = newLink;
		return memory + newLink->start;
	}
	//If the whole list has been travered and nothing has been found and the end is too small 0 is returned
	if (currentLink->start + currentLink->size + newLink->size > 1000) {
		result = 0;
		return 0;
	}
	//Add to the end of the list
	block_num++;
	currentLink->next = newLink;
	newLink->next = NULL;
	newLink->start = currentLink->start + currentLink->size;
	result = memory + newLink->start;
	return memory + newLink->start;
}


void * add_node(struct Link * newLink) {
	int flag = 0;
	void * result;
	struct Link * prevLink;
	struct Link * currentLink = head;
	//If there's a large enough space in front of the head link
	if (currentLink->start >= newLink->size) {
		newLink->start = 0;
		newLink->next = currentLink;
		head = newLink;
		result = memory + newLink->start;
		return memory + newLink->start;
	}
	//If the head is the only link
	if (currentLink->next == NULL) {
		newLink ->start = currentLink->start + currentLink->size;
		currentLink->next = newLink;
		newLink -> next = NULL;
		result =  memory + newLink->start;
		block_num++;
		return memory + newLink->start;
	}
	//Loop through and search for a gap large enough
	while (currentLink->next != NULL) {
		prevLink = currentLink;
		currentLink = currentLink -> next;
		if (currentLink->start-(prevLink->start + prevLink->size) >= newLink->size) {
			newLink ->start = prevLink->start+prevLink->size;
			newLink->next = currentLink;
			prevLink->next = newLink;
			result =  memory + newLink->start;
			block_num++;
			return memory + newLink->start;
		}
	}
	//If there's not enough room in the list
	if (currentLink->start + currentLink->size + newLink->size > 1000) {
		result = 0;
		return 0;
	}
	//If there's enough room put it on the end
	else {
		block_num++;
		currentLink->next = newLink;
		newLink -> next = NULL;
		newLink ->start = currentLink->start + currentLink->size;
		result =  memory + newLink->start;
		return memory + newLink->start;
	}
}

void * bvMalloc(int size, int bestFit) {
	//If its the first call of the function malloc memory, create a link, set head to the new link
	if (initialized == 0) {
		initialized = 1;
		memory=malloc(1000); 
		head = (struct Link *)malloc(sizeof(struct Link));
		head->start = 0;
		head->size = size;
		head->next = NULL;
		block_num++;
		starting_address = ((long long)memory);
		return memory;
	}
	else {
		//If it's not first function call create a link and send it to the corresponding function
		struct Link* node = (struct Link *)malloc(sizeof(struct Link));
		node->size = size;
		if(bestFit == 1) {
			return best_fit(node);
		}
		else {
			return add_node(node);
		}
	}
}

void bvFree(void * address) {
	long long virtual_address = ((long long)address) - starting_address;
	struct Link * prevLink;
	struct Link * currentLink = head;
	//If the head is being removed
	if (head->start == virtual_address) {
		head = head->next;
		free(currentLink);
	}
	else {
		//Find the block who's ->start corresponds to the virtual_address and free it
		while (currentLink->next != NULL) {
			prevLink = currentLink;
			currentLink = currentLink->next;
			if (currentLink->start == virtual_address) {
				prevLink->next = currentLink->next;
				free(currentLink);
				break;
			}
		}
	}
}
