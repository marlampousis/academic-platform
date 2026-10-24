# Academic Platform - Test Data

This document contains all test credentials, sample payloads and API examples used during the development of the Academic Platform backend.

---

# Authentication

## Test User

```json
{
  "email": "mario@test.com",
  "password": "Test123!"
}
```

---

## Login

**Endpoint**

```http
POST /auth/login
```

## Authorization

After login copy the access token and use:

```
Bearer <access_token>
```

Example:

```
Bearer eyJhbGciOiJIUzI1NiIs...
```

---

# Academic Profile

## Endpoint

```http
POST /profiles/
```

```json
{
  "institution_id": 1,
  "department_id": 1,
  "academic_rank": "Assistant Professor",
  "specialization": "Artificial Intelligence",
  "research_areas": "LLMs, NLP, RAG",
  "orcid_id": "0000-0002-1825-0097",
  "biography": "Researcher in AI"
}
```

---

# Degrees

## Endpoint

```http
POST /degrees/
```

```json
{
  "degree_type": "MSc",
  "title": "MSc in Finance and Banking",
  "field_of_study": "Finance",
  "institution_name": "Athens University of Economics and Business",
  "country": "Greece",
  "start_year": 2024,
  "end_year": 2026
}
```

---

# Publications

## Endpoint

```http
POST /publications/
```

```json
{
  "title": "AI-Powered Academic Qualification Management",
  "abstract": "This paper explores the use of intelligent systems for academic profile management.",
  "publication_type": "Journal Article",
  "publication_year": 2025,
  "doi": "10.1234/example.2025.001",
  "journal_name": "Journal of Academic Information Systems",
  "conference_name": null,
  "publisher": "Example Publisher",
  "citation_count": 0,
  "openalex_id": null,
  "orcid_work_id": null
}
```

---

# Research Projects

## Endpoint

```http
POST /research-projects/
```

```json
{
  "title": "AI-Powered Academic Evaluation Platform",
  "acronym": "AI-AEP",
  "funding_program": "Horizon Europe",
  "funding_organization": "European Commission",
  "role": "Principal Investigator",
  "status": "Ongoing",
  "funding_amount": 1250000.50,
  "currency": "EUR",
  "start_date": "2025-01-01",
  "end_date": "2028-12-31",
  "project_identifier": "HE-2025-AI-AEP-001",
  "website_url": "https://example-project.eu",
  "keywords": "AI, Academic Evaluation, LLMs, RAG",
  "description": "Research project focused on intelligent systems for academic evaluation."
}
```

---

# Teaching Experience

## Endpoint

```http
POST /teaching-experience/
```

```json
{
  "course_title": "Machine Learning",
  "institution_name": "Athens University of Economics and Business",
  "department_name": "Department of Informatics",
  "academic_year": "2025-2026",
  "semester": "Spring",
  "course_level": "Postgraduate",
  "teaching_role": "Instructor",
  "hours_per_week": 3,
  "description": "Graduate course on machine learning methods and applications."
}
```

---

# API Testing Order

For a fresh database execute the endpoints in the following order:

1. Register a user
2. Login
3. Create Institution (or run Seeder)
4. Create Department
5. Create Academic Profile
6. Create Degree
7. Create Publication
8. Create Research Project
9. Create Teaching Experience

---

# Database Tables

Current backend database structure:

- users
- institutions
- departments
- academic_profiles
- degrees
- publications
- research_projects
- teaching_experience

---

# Notes

- All protected endpoints require JWT authentication.
- Every Degree, Publication, Research Project and Teaching Experience belongs to one Academic Profile.
- Every Academic Profile belongs to one User.
- Institutions must exist before creating an Academic Profile.
- Departments must exist before creating an Academic Profile.