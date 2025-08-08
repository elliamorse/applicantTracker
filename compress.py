import requests
import json
from secrets import AIRTABLE_BASE_ID, AIRTABLE_API_KEY

#Your Airtable config
HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

#Table names
APPLICANTS_TABLE = 'Applicants'
PERSONAL_TABLE = 'Personal Details'
EXPERIENCE_TABLE = 'Work Experience'
SALARY_TABLE = 'Salary Preferences'

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
    #print(records)
    return records

def build_json_for_applicant(applicant_id, personal_map, experience_map, salary_map):
    personal = personal_map.get(applicant_id, {}) 
    print(personal)
    experience = experience_map.get(applicant_id, [])
    salary = salary_map.get(applicant_id, {})

    compressed = {
        'personal': personal,
        'experience': experience,
        'salary': salary
    }
    print(compressed)
    return compressed

def update_applicant_record(applicant_id, json_obj):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{APPLICANTS_TABLE}/{applicant_id}'
    data = {
        "fields": {
            "Compressed JSON": json.dumps(json_obj)
        }
    }
    requests.patch(url, headers=HEADERS, json=data)

def main():
    applicants = get_records(APPLICANTS_TABLE)
    personal_details = get_records(PERSONAL_TABLE)
    experiences = get_records(EXPERIENCE_TABLE)
    salaries = get_records(SALARY_TABLE)

    #Build maps
    personal_map = {
        r['fields']['ApplicantID'][0]: {
            'name': r['fields'].get('Full Name', ''),
            'location': r['fields'].get('Location', '')
        } for r in personal_details if 'ApplicantID' in r['fields']
    }

    experience_map = {}
    for r in experiences:
        for app_id in r['fields'].get('ApplicantID', []):
            experience_map.setdefault(app_id, []).append({
                'company': r['fields'].get('Company', ''),
                'title': r['fields'].get('Title', '')
            })

    salary_map = {
        r['fields']['ApplicantID'][0]: {
            'rate': r['fields'].get('Rate', ''),
            'currency': r['fields'].get('Currency', ''),
            'availability': r['fields'].get('Availability', '')
        } for r in salaries if 'ApplicantID' in r['fields']
    }


    #Update each applicant with compressed JSON
    for applicant in applicants:
        applicant_id = applicant['id']
        linked_id = applicant['fields'].get('ApplicantID')
        print('Processing applicant_id:', applicant_id, 'linked_id:', linked_id)
        if linked_id:
            json_obj = build_json_for_applicant(linked_id, personal_map, experience_map, salary_map)
            update_applicant_record(applicant_id, json_obj)

if __name__ == '__main__':
    main()
