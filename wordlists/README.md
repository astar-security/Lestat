# Wordlist How to
Some wordlists can be downloaded from [here](https://bonny.astar.org/wordlist.zip)  

Two other wordlists must be generated.  

### creating wl_0_company_name.txt
Simply put the name of your company inside (don't worry about the lowercase/uppercase).
```
echo EvilCorp > wl_0_company_name.txt
```

### creating wl_1_company_context_related
Put 3 or 4 words related to your company in a `words.txt` file (the name of your company, your ZIP code, the town of the company, what it sells, ...).  

Then, use a mangler to derivate and combine these words with common variations (l33t, mix case, special char, etc.).  
We provide our own tool : `asmangler` (be patient, the processing is low)
```
python3 asmangler -f words.txt > wl_1_company_context_related.txt
```
