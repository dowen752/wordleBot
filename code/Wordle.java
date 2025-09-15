

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import java.util.Scanner;


// This is a simple Java implementation of a Wordle-like game.
// The game randomly selects a 5-letter word from a file and allows the user to guess.

class Wordle{
    public static void main(String[] args) throws IOException {
        List<String> words = Files.readAllLines(Paths.get("code/words.txt"));
        Scanner scan = new Scanner(System.in);
        Random random = new Random();
        String GREEN = "\u001B[42m"; // Color codes for characters depending on if char is correct, in wrong spot, or not in the word
        String YELLOW = "\u001B[43m";
        String RESET = "\u001B[0m";


        String correct = words.get(random.nextInt(words.size()));
        String guess = "";
        List<String> guessed = new ArrayList<>();

        System.out.println("WORDLE\n------\n");
        for(int round = 0; round < 6; round++){
            System.out.println("Please guess.\n-------------");
            System.out.flush();
            while(true){
                if(scan.hasNextLine()){
                    guess = scan.nextLine().toUpperCase();
                }

                if(guess.length() == 5){
                    break;
                }
                else{
                    System.out.println("Please input only 5 letter words.");
                }
            }

            // --------------
            // Start of check
            // --------------

            // Count letters in answer
            int[] answerCounts = new int[26];
            for (int i = 0; i < 5; i++) {
                char ch = correct.charAt(i);
                answerCounts[ch - 'A']++;
            }

            // First pass: default all to B
            char[] feedback = new char[5];
            for (int i = 0; i < 5; i++) {
                feedback[i] = 'B';
            }

            // First pass: mark greens
            for (int i = 0; i < 5; i++) {
                if (guess.charAt(i) == correct.charAt(i)) {
                    feedback[i] = 'G';
                    answerCounts[guess.charAt(i) - 'A']--;
                }
            }

            // Second pass: mark yellows
            for (int i = 0; i < 5; i++) {
                if (feedback[i] == 'G') continue;
                char gch = guess.charAt(i);
                if (answerCounts[gch - 'A'] > 0) {
                    feedback[i] = 'Y';
                    answerCounts[gch - 'A']--;
                }
            }

            // Print colored feedback
            for (int i = 0; i < 5; i++) {
                char ch = guess.charAt(i);
                if (feedback[i] == 'G') {
                    System.out.print(GREEN + ch + RESET);
                } else if (feedback[i] == 'Y') {
                    System.out.print(YELLOW + ch + RESET);
                } else {
                    System.out.print(ch);
                }
                if (guessed.indexOf("" + ch) == -1) {
                    guessed.add("" + ch);
                }
            }
            System.out.println("\nUsed characters: " + guessed + "\n");

            if (guess.equals(correct)) {
                System.out.println("\nYOU WIN TWIN!!!!\n\n O_O");
                break;
            }
        }
        if(!guess.equals(correct)){
            System.out.println("The correct answer was: " + correct);
        }


        scan.close();
    }
}