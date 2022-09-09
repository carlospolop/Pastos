import argparse
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from time import sleep
from colorama import Fore
from colorama import Style
from typing import (
    Dict,
    List,
    Optional,
    Any,
    Tuple
)



# 100 requests per minute and api key, but each request takes some time so lets give some extra 100
RATE_LIMIT_SLEEP = 60/200


def google_search(search_term: str, gcse_id: str, api_key: str, debug:bool, **kwargs) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Perform a search inside a google custom search engine ID
        """

        sleep(RATE_LIMIT_SLEEP)

        other_args = ""
        if kwargs:
            for key, value in kwargs.items():
                other_args += f"&{key}={value}"

        url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={gcse_id}&q={search_term}{other_args}"

        if debug:
            print(f"[d] Debug: {url}")

        try:
            res = requests.get(url).json()
        except Exception as e:
            if "Remote end closed connection without" in str(e):
                print("Found 'Remote end closed connection without' error, retrying in 3 secs")
                sleep(3)
                return google_search(search_term=search_term, gcse_id=gcse_id, api_key=api_key, debug=debug, siterestrict=siterestrict, **kwargs)

            else:
                print(f"Error performing request: {e}")
                return None, url

        if "error" in res and "code" in res["error"] and int(res["error"]["code"]) == 429:
            print(f"429 code in google search. Sleeping 10s and retrying. Error: {res['error'].get('message', '')}")
            sleep(10)
            return google_search(search_term=search_term, gcse_id=gcse_id, api_key=api_key, debug=debug, siterestrict=siterestrict, **kwargs)

        total_results = res['searchInformation']['totalResults'] if 'searchInformation' in res and 'totalResults' in res['searchInformation'] else 0
        items = res['items'] if "items" in res else []

        res = {
            "totalResults": total_results,
            "items": items
        }

        return res, url


def req_query(query: str, gcse_id: str, api_key: str, debug: bool, start: int = 1, max_results: int = 20) -> Tuple[Optional[List[Any]], str]:
        """
        Search a query inside a google custom search engine ID and if more results get them
        """

        response, url = google_search(query, gcse_id, api_key, debug, num=10, start=start)

        if not response:
            return None, url

        results = response["items"]
        if int(response["totalResults"]) >= start+10 and start+10 < max_results: # Max of 20 results in total
            results += req_query(query, gcse_id, api_key, debug, start=start+10, max_results=max_results)[0]

        return results, url


def check_pastes(searches: List[str], gcse_id: str, api_key: str, debug:bool, out_json_file:str) -> None:
    json_results = []

    for search in searches:
        search = f'"{search}"'

        print(f"Searching: {Fore.GREEN}{search}{Style.RESET_ALL}")
        print("")

        results, url = req_query(search, gcse_id, api_key, debug)

        if not results:
            continue
        
        # If here, something was found
        json_results.append({
            "name": search,
            "links": [ {"link": res["link"], "snippet": res["snippet"]} for res in results]
        })
    
        print("")
        print(f"{Fore.YELLOW}[u] {Fore.BLUE}{search}")
        print(f"{Fore.YELLOW}[i] {Fore.BLUE}Links:{Style.RESET_ALL}")
        for res in results:
            print(res["link"])

        print("")
        
        print("==================================")
        print("")

    if out_json_file:
        with open("results.json", "w") as f:
            json.dump(json_results, f)

def main():
    parser = argparse.ArgumentParser(description='Search google dorks in the specified GCSE id')
    cseid = "737425e5642448a6c" # My custom search engine id with domains used for pastes
    parser.add_argument('--api-key', help='API key', required=True)
    parser.add_argument('--search', help='Comma Separated list of things to search in paste webs', required=True)
    parser.add_argument('--debug', help='Debug', default=False, action='store_true')
    parser.add_argument('--json-file', help='Print only json results at then end', default=False, action='store_true')

    args = parser.parse_args()
    api_key = args.api_key
    searches = args.search.split(",")
    debug = args.debug
    out_json_file = args.json_file

    # Search each search
    check_pastes(searches, cseid, api_key, debug, out_json_file)


if __name__ == "__main__":
    main()
