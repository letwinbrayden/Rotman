import requests # step 1
API_KEY = {'X-API-key': '78DZHH2V'} # step 2
def main():
    with requests.Session() as s: # step 3
        s.headers.update(API_KEY) # step 4
        resp = s.get('http://localhost:9999/v1/case') # step 5
    if resp.ok: # step 6
        case = resp.json() # step 7
        tick = case['tick'] # accessing the 'tick' value that was returned
        print('The case is on tick', tick) # step 8
if __name__ == '__main__':
    main()
