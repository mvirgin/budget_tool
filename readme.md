Thrown together prototype for a budgeting tool.  
My bank lets me export transactions as a csv.  
Put two csv's (from both my bank accounts) into input_csvs folder (two is hardcoded - again, thrown together)  
run update_from_input.py - this will modify buckets.json based off the input csvs  
Templates for what my bank csvs look like (history_template.csv) and what buckets.json should look like 
(buckets_template.json) are provided. Modify to suit your preferences but the code will likely need to be 
modified as well. (Again, this is very thrown together atm).  

Note: Potential to use Teller (https://teller.io/docs/api/account/transactions) 
to link my bank account and then just use API calls to get transaction info instead 
of having to manually download the csvs. Worth looking into once I start hosting this 
somewhere so that I can update buckets while I'm out and about.