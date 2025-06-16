package wordleInJava.code;

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
        String GREEN = "\u001B[42m";
        String YELLOW = "\u001B[43m";
        String GRAY = "\u001B[100m";
        String RESET = "\\u001B[0m";


        String correct = words.get(random.nextInt(words.size()));
        String guess = "";


        System.out.println("WORDLE\n------\n");
        for(int round = 0; round < 6; round++){
            System.out.println("Please guess.\n-------------");
            guess = scan.nextLine().toUpperCase();
            if(guess.equals(correct)){
                System.out.println("\nYOU WIN TWIN!!!!\n\n O_O");
                break;
            }
            else{
                String output = "";
                for(int c = 0; c < 6; c++){
                    char gChar = guess.charAt(c);
                    char cChar = correct.charAt(c);
                    if(gChar == cChar){
                        String oChar = GREEN + cChar + RESET;
                        output += oChar;
                    }
                    else{
                        output += "_";
                    }
                }
                // for(int i = 0; i < 6; i++){
                    
                // }
            }

        }


        scan.close();
    }
}