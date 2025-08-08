import requests
import json
from secrets import AIRTABLE_BASE_ID, AIRTABLE_API_KEY

HEADERS = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json'
}

#Tables
APPLICANTS_TABLE = 'Applicants'
PERSONAL_TABLE = 'Personal Details'
EXPERIENCE_TABLE = 'Work Experience'
SALARY_TABLE = 'Salary Preferences'

def get_records(table):
    records = []
    offset = None
    while True:
        url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}'
        params = {'offset': offset} if offset else {}
        res = requests.get(url, headers=HEADERS, params=params)
        data = res.json()
        if 'records' not in data:
            print(f"Error loading {table}:", data)
            break
        records.extend(data['records'])
        offset = data.get('offset')
        if not offset:
            break
    return records

def delete_record(table, record_id):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}/{record_id}'
    requests.delete(url, headers=HEADERS)

def create_record(table, fields):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}'
    data = {"fields": fields}
    requests.post(url, headers=HEADERS, json=data)

def update_record(table, record_id, fields):
    url = f'https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{table}/{record_id}'
    data = {"fields": fields}
    requests.patch(url, headers=HEADERS, json=data)

def upsert_child_records():
    applicants = get_records(APPLICANTS_TABLE)
    personal = get_records(PERSONAL_TABLE)
    experience = get_records(EXPERIENCE_TABLE)
    salary = get_records(SALARY_TABLE)

    #Build maps from child records
    personal_by_applicant = {r['fields']['ApplicantID'][0]: r for r in personal if 'ApplicantID' in r['fields']}
    experience_by_applicant = {}
    for r in experience:
        for aid in r['fields'].get('ApplicantID', []):
            experience_by_applicant.setdefault(aid, []).append(r)
    salary_by_applicant = {r['fields']['ApplicantID'][0]: r for r in salary if 'ApplicantID' in r['fields']}

    for a in applicants:
        applicant_id = a['id']
        app_key = a['fields'].get('ApplicantID')
        compressed = a['fields'].get('Compressed JSON')
        if not (app_key and compressed):
            continue

        try:
            parsed = json.loads(compressed)
        except Exception as e:
            print(f"Invalid JSON for {applicant_id}: {e}")
            continue

        #Update Personal Details
        personal_data = parsed.get('personal', {})
        fields = {
            'Full Name': personal_data.get('name', ''),
            'Location': personal_data.get('location', ''),
            'Applicant ID': [app_key]
        }
        if app_key in personal_by_applicant:
            update_record(PERSONAL_TABLE, personal_by_applicant[app_key]['id'], fields)
        else:
            create_record(PERSONAL_TABLE, fields)

        #Update Salary Preferences
        salary_data = parsed.get('salary', {})
        salary_fields = {
            'Rate': salary_data.get('rate', ''),
            'Currency': salary_data.get('currency', ''),
            'Availability': salary_data.get('availability', ''),
            'Applicant ID': [app_key]
        }
        if app_key in salary_by_applicant:
            update_record(SALARY_TABLE, salary_by_applicant[app_key]['id'], salary_fields)
        else:
            create_record(SALARY_TABLE, salary_fields)

        #Update Work Experience
        exp_data = parsed.get('experience', [])
        existing_exps = experience_by_applicant.get(app_key, [])

        #Update existing or create new
        for i, exp in enumerate(exp_data):
            fields = {
                'Company': exp.get('company', ''),
                'Title': exp.get('title', ''),
                'Applicant ID': [app_key]
            }
            if i < len(existing_exps):
                update_record(EXPERIENCE_TABLE, existing_exps[i]['id'], fields)
            else:
                create_record(EXPERIENCE_TABLE, fields)

        #Delete extras if too many existing experience rows
        if len(existing_exps) > len(exp_data):
            for r in existing_exps[len(exp_data):]:
                delete_record(EXPERIENCE_TABLE, r['id'])

if __name__ == '__main__':
    upsert_child_records()
