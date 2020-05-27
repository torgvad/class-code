package edu.bvu.algo.huffman;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Scanner;

import edu.bvu.algo.BinaryTree;
//import edu.bvu.algo.huffman.Node;

public class Huffman {

	public class Node {
		private Character data;
		private Integer frequency;
		
		public Node() {
			setChar(' ');
			setFreq(0);
		}
		
		public Node(Character data, Integer frequency) {
			setChar(data);
			setFreq(frequency);
		}
		public Character getChar() {
			return data;
		}
		public Integer getFreq() {
			return frequency;
		}
		
		public void setChar(Character new_data) {
			data = new_data;
		}
		
		public void setFreq(Integer new_freq) {
			frequency = new_freq;
		}
		
		public void printNode() {
			System.out.print(data);
			System.out.print("=");
			System.out.print(frequency);
			System.out.println();
		}
	}

	//Takes two trees and combined them according to their frequencies with a root at the top
	public static BinaryTree<Node> treeCombiner(BinaryTree<Node> Tree1, BinaryTree<Node> Tree2) {
		Integer Tree1Freq = freqCount(Tree1);
		Integer Tree2Freq = freqCount(Tree2);
		Huffman huffm = new Huffman();
		Huffman.Node rootNode = huffm.new Node(Character.MIN_VALUE, 0);
		BinaryTree<Node> root = new BinaryTree<Node>(rootNode);
		if (Tree1Freq >= Tree2Freq) {
			root.setLeft(Tree1);
			root.setRight(Tree2);
		}
		else {
			root.setRight(Tree1);
			root.setLeft(Tree2);
		}
		return root;
	}

	//The codes are stored as a global for encoding
	public static HashMap<Character, String> codes = new HashMap<Character, String>();

	//Goes through a binary tree and assigns each Char to a binary code which is stored in the global var "codes"
	public static void codeGenerator(BinaryTree<Node> t, String code) {
		if (t.getData().getChar() == Character.MIN_VALUE) {
			if (t.getLeft() != null) {
				codeGenerator(t.getLeft(), code + "0");
			}
			if (t.getRight() != null) {
				codeGenerator(t.getRight(), code + "1");
			}
		}
		else {
			if (t.getLeft() == null && t.getRight() == null) {
				codes.put(t.getData().getChar(), code);
			}
			if (t.getLeft() != null) {
				codes.put(t.getData().getChar(), code);
				codeGenerator(t.getLeft(), code + "0");
			}
			if (t.getRight() != null) {
				codes.put(t.getData().getChar(), code);
				codeGenerator(t.getRight(), code + "1");
			}
		}
	}

	//Go through each node and add their frequencies
	public static Integer freqCount(BinaryTree<Node> t) {
		if (t == null) {
			return 0;
		} else if (t.getLeft() == null && t.getRight() == null) {
			Node examinedNode = t.getData();
			return examinedNode.getFreq();
		} else
			return freqCount(t.getLeft()) + freqCount(t.getRight());
	}

	public static ArrayList<Integer> freqs = new ArrayList<Integer>();

	//Take the hashmap of Char to Frequency and turn each into a BianryTree and put into a ArrayList
	public static ArrayList<BinaryTree<Node>> Treeafy(HashMap<Character, Integer> evaluating) {
		// I did want to use a priority queue like stated in class. Though java is too much of an enigma.
		ArrayList<BinaryTree<Node>> ValueHolder = new ArrayList<BinaryTree<Node>>();
		while (evaluating.size() != 0) {
			Character smallest = giveSmallest(evaluating);
			Integer value = evaluating.get(smallest);
			Huffman huffm = new Huffman();
			Huffman.Node treeNode = huffm.new Node(smallest, value);
			BinaryTree<Node> startTree = new BinaryTree<Node>(treeNode);
			ValueHolder.add(startTree);
			freqs.add(value);
			evaluating.remove(smallest);
		}

		return ValueHolder;
	}

	//Give Char with the smallest frequency
	public static Character giveSmallest(HashMap<Character, Integer> evaluating) {
		Integer smallest = 0;
		Character smol_k = ' ';
		Integer current_smol = 0;
		for (HashMap.Entry<Character, Integer> entry : evaluating.entrySet()) {
			Character this_k = entry.getKey();
			current_smol = entry.getValue();
			if (smallest == 0) {
				smallest = current_smol;
				smol_k = this_k;
			}
			if (current_smol < smallest) {
				smallest = current_smol;
				smol_k = this_k;
			}
		}
		return smol_k;
	}

	//Take the file and generate a hashmap of Chars to their Frequency
	public static HashMap<Character, Integer> generateMap(File inputFile) {
		HashMap<Character, Integer> ReturnMap = new HashMap<Character, Integer>();
		BufferedReader reader;
		try {
			reader = new BufferedReader(new FileReader(inputFile));
			String line = reader.readLine();
			while (line != null) {
				for (int i = 0; i != line.length(); i++) {
					if (ReturnMap.containsKey(line.charAt(i))) {
						Integer count = ReturnMap.get(line.charAt(i));
						count++;
						ReturnMap.replace(line.charAt(i), count);
					} else {
						ReturnMap.put(line.charAt(i), 1);
					}
				}
				if (ReturnMap.containsKey('\n')) {
					Integer count = ReturnMap.get('\n');
					count++;
					ReturnMap.replace('\n', count);
				}
				else {
					ReturnMap.put('\n', 1);
				}
				line = reader.readLine();
			}

		} catch (IOException e) {
			e.printStackTrace();
		}
		return (ReturnMap);
	}

	/**
	 * Passed an empty <code>charBitMap</code> and an empty
	 * <code>encodedBits</code>, this method fills them using the specified
	 * <code>inputFile</code>.
	 * <p>
	 * Once filled, <code>charBitMap</code> will be of the form (for example):
	 * 
	 * <pre>
	 * { 'e' = "1", 'a' = "00", 't' = "01" }
	 * </pre>
	 * <p>
	 * And, if <code>inputFile</code> contains "eat", then <code>encodedBits</code>
	 * would contain "10001".
	 * 
	 * @param inputFile
	 * @param charBitMap
	 * @param encodedBits
	 * @throws FileNotFoundException
	 */
	public void generateEncodings(File inputFile, Map<Character, String> charBitMap, StringBuffer encodedBits)
			throws FileNotFoundException {
		// FIXME
		HashMap<Character, Integer> frequencies = generateMap(inputFile);
		BinaryTree<Character> ourTree = new BinaryTree<Character>('a');
		//System.out.println(frequencies);
		ArrayList<BinaryTree<Node>> printing = new ArrayList<BinaryTree<Node>>();
		printing = Treeafy(frequencies);
		for (int i = 0; i != printing.size(); i++) {
			BinaryTree<Node> thisthing = printing.get(i);
			Node anotherthing = thisthing.getData();
			// anotherthing.printNode();
		}
		System.out.println(freqs);
		while (freqs.size() != 0 || printing.size() != 0) {
			int min;
			int indexof;
			if (freqs.size() > 1) {
				min = Collections.min(freqs);
				indexof = freqs.indexOf(min); 
			}
			else {
				break;
			}
			BinaryTree<Node> Tree1 = printing.get(indexof);
			printing.remove(indexof);
			freqs.remove(indexof);
			min = Collections.min(freqs);
			indexof = freqs.indexOf(min);
			BinaryTree<Node> Tree2 = printing.get(indexof);
			printing.remove(indexof);
			freqs.remove(indexof);
			BinaryTree<Node> outTree = treeCombiner(Tree1, Tree2);
			Integer count = freqCount(outTree);
			printing.add(outTree);
			freqs.add(count);
		}
		
		//System.out.println(printing.size());
		codeGenerator(printing.get(0), "");
		for (HashMap.Entry<Character, String> entry : codes.entrySet()) {
			Character this_k = entry.getKey();
			String current_smol = entry.getValue();
			charBitMap.put(this_k, current_smol);
		}
		BufferedReader reader;
		try {
			reader = new BufferedReader(new FileReader(inputFile));
			String line = reader.readLine();
			while (line != null) {
				for (int i = 0; i != line.length(); i++) {
				String encoding = charBitMap.get(line.charAt(i));
				encodedBits.append(encoding);
				}
				encodedBits.append(charBitMap.get('\n'));
				line = reader.readLine();
			}

		} catch (IOException e) {
			e.printStackTrace();
		}
		//System.out.println(codes);
	}

	/**
	 * Passed a filled <code>charBitMap</code> and a filled
	 * <code>encodedBits</code>, this method returns a <code>StringBuffer</code>
	 * object representing the decoded file.
	 * 
	 * @param charBitMap
	 * @param encodedBits
	 * @return
	 * @throws IOException 
	 */
	public StringBuffer interpretBits(Map<Character, String> charBitMap, String encodedBits) throws IOException {
		StringBuffer return_buf = new StringBuffer();
		String examined = "";
		for (int i=0; i != encodedBits.length(); i++) {
			Character oneChar = encodedBits.charAt(i);
			examined = examined + oneChar.toString();
			//System.out.println("HERE");
			//System.out.println(examined);
			for (HashMap.Entry<Character, String> entry : charBitMap.entrySet()) {
				Character this_k = entry.getKey();
				String current_smol = entry.getValue();
				//System.out.println(examined);
				if (current_smol.equals(examined)) {
					return_buf.append(this_k);
					examined = "";
				}
			}
		}
		BufferedWriter writer = new BufferedWriter(new FileWriter("/Users/Vadim/Desktop/output.txt"));
		writer.write(return_buf.toString());
		writer.close();
		return return_buf;
	}

	public static void main(String[] args) throws IOException {
		
		  Huffman huf = new Huffman();
		  
		  File f = new File("/Users/Vadim/Desktop/test.txt"); 
		  HashMap<Character, String> charBitMap = new HashMap<Character, String>(); 
		  StringBuffer bits = new StringBuffer();
		  huf.generateEncodings(f, charBitMap, bits);

		  System.out.println(charBitMap);
		  
		  System.out.println(bits);
		  
		  StringBuffer fileBuf = huf.interpretBits(charBitMap, bits.toString());
		  System.out.println(fileBuf.toString());
		 
	}

}
