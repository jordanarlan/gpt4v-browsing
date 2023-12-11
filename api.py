import requests
from importlib.machinery import SourceFileLoader
import pandas as pd


def get_filtered_results():
    config = SourceFileLoader("config", "config.py").load_module()

    bungie_api_key = config.BUNGIE_API_KEY
    endpoint = "https://www.bungie.net/Platform/Content/Rss/NewsArticles/{pageToken}/"
    page_token = "0"
    include_body = True
    headers = {
        "X-API-Key": bungie_api_key
    }
    params = {
        "includebody": include_body
    }

    results = []
    
    while page_token is not None:
        response = requests.get(endpoint.format(pageToken=page_token), headers=headers, params=params)

        if response.status_code == 200:
            json_response = response.json()
            if 'Response' in json_response and 'NextPaginationToken' in json_response['Response']:
                page_token = json_response['Response']['NextPaginationToken']
                if 'NewsArticles' in json_response['Response']:
                    results.extend(json_response['Response']['NewsArticles'])
                else:
                    print("No NewsArticles found in the response.")
                    break
            else:
                print("No NextPaginationToken found in the response.")
                break
        else:
            print("Error:", response.status_code)
            print("Response:", response.text)
            break
        
    # Desired keys
    keys = ['Title', 'Link', 'PubDate', 'Description']

    # Filtering the results
    filtered_results = [{key: item[key] for key in keys} for item in results]

    # Convert the filtered list into a DataFrame
    df = pd.DataFrame(filtered_results)

    import re
    pattern = r'Update|Hotfix'
    df = df[df['Title'].str.contains(pattern, regex=True, flags=re.IGNORECASE)]
    df = df.iloc[0:25].reset_index()

    base_url = "https://www.bungie.net"

    # Prepending the base URL to each 'Link' in the DataFrame
    df['Link'] = df['Link'].apply(lambda x: base_url + x)

    return df

df = get_filtered_results()

def save_to_csv(df, filename='bungie_news.csv'):
    # Save DataFrame to CSV
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")

save_to_csv(df)
