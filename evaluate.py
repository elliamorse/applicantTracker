
import requests
import json
from secrets import AIRTABLE_BASE_ID, AIRTABLE_API_KEY

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

SHORTLIST_TABLE = 'Shortlisted Leads'

TIER_1_COMPANIES = {'Google', 'Meta', 'OpenAI'}

ALLOWED_COUNTRIES = {'US', 'United States', 'Canada', 'UK', 'Germany', 'India'}

def get_records(table):
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

def years_experience(experience_list):
    # naive example: sum durations if available, or count entries
    return sum(exp.get('years', 1) for exp in experience_list)  # fallback 1 year each

def worked_at_tier1(experience_list):
    return any(exp.get('company', '') in TIER_1_COMPANIES for exp in experience_list)

def location_allowed(location):
    # normalize country names if needed
    return any(loc in location for loc in ALLOWED_COUNTRIES)

def should_shortlist(applicant_json):
    personal = applicant_json.get('personal', {})
    experience = applicant_json.get('experience', [])
    salary = applicant_json.get('salary', {})

    exp_years = years_experience(experience)
    tier1 = worked_at_tier1(experience)
    rate_ok = float(salary.get('rate', float('inf'))) <= 100
    avail_ok = float(salary.get('availability', 0)) >= 20
    loc_ok = location_allowed(personal.get('location', ''))

    meets_exp = (exp_years >= 4) or tier1
    meets_comp = rate_ok and avail_ok
    meets_loc = loc_ok

    all_good = meets_exp and meets_comp and meets_loc

    reason_parts = []
    if meets_exp:
        reason_parts.append(f"Experience ok ({exp_years} years or Tier-1)")
    else:
        reason_parts.append(f"Experience NOT ok ({exp_years} years, no Tier-1)")

    if meets_comp:
        reason_parts.append(f"Compensation ok (rate {salary.get('rate')} USD, availability {salary.get('availability')} hrs)")
    else:
        reason_parts.append(f"Compensation NOT ok (rate {salary.get('rate')}, availability {salary.get('availability')})")

    if meets_loc:
        reason_parts.append(f"Location ok ({personal.get('location')})")
    else:
        reason_parts.append(f"Location NOT ok ({personal.get('location')})")

    score_reason = "; ".join(reason_parts)

    return all_good, score_reason

def create_shortlist_record(applicantID, compressed_json, score_reason):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{SHORTLIST_TABLE}'
    data = {
        "fields": {
            "ApplicantID": [applicantID],
            "Compressed JSON": json.dumps(compressed_json),
            "Score Reason": score_reason
        }
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        print(f"Shortlisted applicant {applicantID}")
    else:
        print(f"Failed to shortlist {applicantID}: {response.text}")


def evaluate_and_shortlist(applicants):
    for applicant in applicants:
        applicant_id = applicant['id']
        compressed_json_str = applicant['fields'].get('Compressed JSON')
        if not compressed_json_str:
            continue
        try:
            compressed_json = json.loads(compressed_json_str)
        except json.JSONDecodeError:
            continue

        meets_criteria, reason = should_shortlist(compressed_json)
        if meets_criteria:
            create_shortlist_record(applicant_id, compressed_json, reason)
        else:
            print(f"Applicant {applicant_id} not shortlisted: {reason}")


if __name__ == '__main__':

    applicants = get_records('Applicants')
    evaluate_and_shortlist(applicants)