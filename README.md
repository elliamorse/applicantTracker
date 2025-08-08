# Airtable Contractor Application Data Model & Automation

## Overview
This project designs an Airtable-based data model and automation system for managing contractor applications. It provides a structured, multi-table form flow and integrates local Python scripts to compress, store, and decompress application data. The system also includes automated shortlisting, candidate evaluation, and enrichment using an LLM endpoint.

## Goals
- Collect contractor-application data through a structured, multi-table Airtable form flow  
- Use a local Python script to compress collected data into a single JSON object for storage and routing  
- Use a local Python script to decompress JSON back into normalized tables for editing  
- Auto-shortlist promising candidates based on multi-factor rules  
- Use an LLM endpoint to evaluate, enrich, and sanity-check each application  

## Airtable Schema Setup
1. **Create Your Base**
   - Log in to Airtable or create an account.  
   - Start with a blank base.  
   - Understand Airtable headers (naming and assigning data types).  

2. **Build the Applicants Table**
   - Create this table manually to understand the setup process.  

3. **Generate Remaining Tables**
   - Copy and paste the remaining four table definitions into **Omni** (Airtable’s AI) to generate them automatically.  
   - Confirm table names, key fields, and relationships.  

4. **Schema Structure**
   - `Applicants` is the parent table.  
   - Three linked child tables: `Personal Details`, `Work Experience`, and `Salary Preferences`.  
   - One helper table: `Shortlisted Leads`.  
   - All child tables link to Applicants via `Applicant ID`.

## Tables & Fields

| Table               | Key Fields | Notes |
|---------------------|-----------|-------|
| **Applicants (parent)** | Applicant ID (primary), Compressed JSON, Shortlist Status, LLM Summary, LLM Score, LLM Follow-Ups | One row per applicant; stores compressed JSON + LLM outputs |
| **Personal Details** | Full Name, Email, Location, LinkedIn, (linked to Applicant ID) | One-to-one with Applicants |
| **Work Experience** | Company, Title, Start, End, Technologies, (linked to Applicant ID) | One-to-many |
| **Salary Preferences** | Preferred Rate, Minimum Rate, Currency, Availability (hrs/wk), (linked to Applicant ID) | One-to-one |
| **Shortlisted Leads** | Applicant (link to Applicants), Compressed JSON, Score Reason, Created At | Auto-populated when rules are met |

## Automation Flow
1. **Data Collection**  
   Contractors complete the multi-table form flow in Airtable.

2. **Compression**  
   Local Python script converts normalized tables into a single compressed JSON object.

3. **Storage & Routing**  
   Compressed JSON stored in `Applicants` table and routed as needed.

4. **Decompression**  
   Local Python script restores JSON into Airtable’s normalized table structure for editing.

5. **Auto-Shortlisting**  
   Rule-based automation moves candidates into `Shortlisted Leads` when criteria are met.

6. **LLM Evaluation**  
   LLM endpoint reviews each application, produces a summary, assigns a score, and identifies follow-up needs.
