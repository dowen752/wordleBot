

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Random;
import java.util.Scanner;

class Wordle{
    public static void main(String[] args) throws IOException {
        List<String> words = Files.readAllLines(Paths.get("wordleInJava/code/words.txt"));
        Scanner scan = new Scanner(System.in);
        Random random = new Random();
        String GREEN = "\u001B[42m"; // Color codes for characters depending on if char is correct, in wrong spot, or not in the word
        String YELLOW = "\u001B[43m";
        String GRAY = "\u001B[100m";
        String RESET = "\u001B[0m";


        String correct = words.get(random.nextInt(words.size()));
        String guess = "";


        System.out.println("WORDLE\n------\n");
        for(int round = 0; round < 6; round++){
            System.out.println("Please guess.\n-------------");
            while(true){
                guess = scan.nextLine().toUpperCase();

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

            
            for(int c = 0; c < 5; c++){  // Char is green if correct char in correct spot
                if(guess.substring(c, c+1).equals(correct.substring(c, c+1))){
                    System.out.print(GREEN + guess.substring(c, c+1) + RESET);
                }
                else if(correct.indexOf(guess.substring(c, c+1)) > -1){
                    System.out.print(YELLOW + guess.substring(c, c+1) + RESET);
                }
                else{
                    System.out.print(guess.substring(c, c+1));
                }
            }
            System.out.println("");

            if(guess.equals(correct)){
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