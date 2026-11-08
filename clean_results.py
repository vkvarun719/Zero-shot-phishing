import pandas as pd

def clean_evaluation_results():
    input_path = "evaluated_results.csv"
    output_path = "clean_evaluated_results.csv"
    
    try:
        # Load the evaluated results
        df = pd.read_csv(input_path)
        
        # Filter out rows where predicted_label is -1 (error/quota-exhausted rows)
        if 'predicted_label' in df.columns:
            cleaned_df = df[df['predicted_label'] != -1].copy()
            
            # Save to a clean CSV file
            cleaned_df.to_csv(output_path, index=False)
            print(f"Success! Cleaned data saved to {output_path}.")
            print(f"Total valid samples retained: {len(cleaned_df)} out of {len(df)}")
        else:
            print("Error: 'predicted_label' column not found in CSV.")
            
    except Exception as e:
        print(f"An error occurred while cleaning the CSV: {e}")

if __name__ == "__main__":
    clean_evaluation_results()