from secrets import AIRTABLE_BASE_ID, AIRTABLE_API_KEY, OPENAI_API_KEY
import requests
import time
import re

import openai
openai.api_key = OPENAI_API_KEY

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}
print("Testing")

def get_records(table):
    print(f"Fetching records from {table}...")
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}'
    records = []
    offset = None
    while True:
        params = {}
        if offset:
            params['offset'] = offset
        response = requests.get(url, headers=HEADERS, params=params).json()
        if 'records' not in response:
            print(f"Error fetching records from {table}:", response)
            break
        records.extend(response['records'])
        offset = response.get('offset')
        if not offset:
            break
    return records

def build_prompt(compressed_json):
    return f"""
You are a recruiting analyst. Given this JSON applicant profile, do four things:
1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

JSON Input:
{compressed_json}

Return exactly:
Summary: <text>
Score: <integer>
Issues: <comma-separated list or 'None'>
Follow-Ups: <bullet list>
"""

from openai import OpenAI

client = OpenAI(api_key=OPENAI_API_KEY)

def call_llm(prompt, max_retries=3):
    print("Calling LLM with prompt:", prompt)
    for i in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            time.sleep(2 ** i)
    return "LLM call failed"


if __name__ == '__main__':
    applicants = get_records('Applicants')
    print(f"Found {len(applicants)} applicants to evaluate")
    for applicant in applicants:
        compressed_json = applicant['fields'].get('Compressed JSON')
        if not compressed_json:
            print(f"Skipping applicant {applicant['id']} - no compressed JSON")
            continue

        prompt = build_prompt(compressed_json)
        llm_response = call_llm(prompt)

        # Parse the LLM response with regex for resilience
        try:
            print("Parsing LLM response...\n" + llm_response)

            summary_match = re.search(r'Summary:\s*(.*)', llm_response)
            score_match = re.search(r'Score:\s*(\d+)', llm_response)
            issues_match = re.search(r'Issues:\s*(.*)', llm_response)
            followups_match = re.search(r'Follow-Ups:\s*(.*)', llm_response, re.DOTALL)

            if not all([summary_match, score_match, issues_match, followups_match]):
                raise ValueError("Missing one or more expected fields in LLM response")

            summary = summary_match.group(1).strip()
            score = int(score_match.group(1).strip())
            issues = issues_match.group(1).strip()
            follow_ups = followups_match.group(1).strip()

        except Exception as e:
            print(f"Error parsing LLM response for {applicant['id']}: {e}")
            continue

        # This is where you'd update Airtable or do something with the result
        print(f"Applicant {applicant['id']} Summary: {summary}, Score: {score}, Issues: {issues}, Follow-Ups: {follow_ups}")
