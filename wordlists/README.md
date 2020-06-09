# Wordlist How to
Only the small wordlists are stored here.  
You can find the others there:
- [wl_3_all_common.txt](https://bonny.astar.org/wl_3_all_common.zip)
- [wl_3_locale_common.txt](https://bonny.astar.org/wl_3_locale_common.zip)

Some other wordlists must be generated.  

### creating wl_0_company_name.txt
Simply put the name of your company inside.

### creating wl_1_company_context_related
Put 3 or 4 words related to your company in a `words.txt` file (the name of your company, your ZIP code, the town of the company, what it sells, ...).  

Then, use a mangler to derivate and combine these words with common variations (l33t, mix case, special char, etc.).  
We provide our own tool : `asmangler` (be patient, the processing is low)
```
python3 asmangler -f words.txt > wl_1_company_context_related.txt
```
