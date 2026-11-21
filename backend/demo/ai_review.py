import json
import streamlit as st
import requests
from copy import deepcopy

COLLECTIONS = {
    "degrees": "Degrees",
    "publications": "Publications",
    "research_projects": "Research Projects",
    "teaching_experience": "Teaching Experience",
}

DECISIONS = [
    "NOT_REVIEWED",
    "ACCEPT",
    "EDIT",
    "REJECT",
]


def candidate_ai_review_page(api_request, display_api_error):
    st.subheader("AI CV Extraction Review")
    st.caption(
        "Review AI suggestions before they become official "
        "academic credentials."
    )

    # PDF/DOCX upload workflow
    st.markdown("### Upload an Academic CV")

    uploaded_cv = st.file_uploader(
        "Select a PDF or DOCX academic CV",
        type=["pdf", "docx"],
        key="ai_cv_document_upload",
        help="Maximum file size: 5 MB",
    )

    if st.button(
        "Extract Credentials from Document",
        type="primary",
        disabled=uploaded_cv is None,
        key="ai_upload_extract_button",
    ):
        if uploaded_cv is not None:
            if uploaded_cv.size > 5 * 1024 * 1024:
                st.error("The file exceeds the 5 MB limit.")
            else:
                try:
                    with st.spinner(
                        "Reading document and extracting credentials..."
                    ):
                        response = api_request(
                            "POST",
                            "/ai/extractions/upload",
                            files={
                                "file": (
                                    uploaded_cv.name,
                                    uploaded_cv.getvalue(),
                                    uploaded_cv.type
                                    or "application/octet-stream",
                                )
                            },
                            timeout=120,
                        )

                    if response.status_code == 201:
                        result = response.json()
                        new_id = result["artifact_id"]

                        st.session_state[
                            "ai_review_selected_id"
                        ] = new_id

                        st.session_state[
                            "ai_review_artifact_number_input"
                        ] = int(new_id)

                        loaded = api_request(
                            "GET",
                            f"/ai/extractions/{new_id}",
                        )

                        if loaded.status_code == 200:
                            st.session_state[
                                "ai_review_artifact"
                            ] = loaded.json()

                            st.session_state[
                                "ai_review_upload_message"
                            ] = (
                                f"Document uploaded successfully. "
                                f"Artifact #{new_id} is ready for review."
                            )

                            st.rerun()
                        else:
                            display_api_error(loaded)
                    else:
                        display_api_error(response)

                except requests.RequestException as exc:
                    st.error(
                        f"Document upload failed: {exc}"
                    )

    upload_message = st.session_state.pop(
        "ai_review_upload_message",
        None,
    )

    if upload_message:
        st.success(upload_message)

    # SECTION 1: Create a new AI extraction
    st.markdown("### Create a new AI extraction")

    with st.form("new_ai_extraction_form"):
        cv_text = st.text_area(
            "Paste your academic CV",
            height=220,
            placeholder=(
                "Include your academic degrees, "
                "publications, research projects "
                "and teaching experience..."
            ),
            max_chars=40000,
        )

        create_clicked = st.form_submit_button(
            "Extract credentials with AI",
            type="primary",
        )

    if create_clicked:
        if not cv_text.strip():
            st.warning("Please enter your CV text.")
        else:
            try:
                with st.spinner(
                    "Extracting academic credentials..."
                ):
                    response = api_request(
                        "POST",
                        "/ai/extractions",
                        json={"cv_text": cv_text},
                        timeout=120,
                    )

                if response.status_code == 201:
                    created = response.json()
                    new_id = created["artifact_id"]

                    st.session_state[
                        "ai_review_selected_id"
                    ] = new_id

                    st.session_state[
                        "ai_review_artifact_number_input"
                    ] = int(new_id)

                    loaded = api_request(
                        "GET",
                        f"/ai/extractions/{new_id}",
                    )

                    if loaded.status_code == 200:
                        st.session_state[
                            "ai_review_artifact"
                        ] = loaded.json()
                        st.rerun()
                    else:
                        display_api_error(loaded)
                else:
                    display_api_error(response)

            except requests.RequestException as exc:
                st.error(
                    f"Could not connect to the AI service: {exc}"
                )

    # SECTION 2: Load an existing extraction
    st.divider()

    st.markdown("### Load an existing extraction")

    # Initialize the artifact ID input once.
    if "ai_review_artifact_number_input" not in st.session_state:
        st.session_state[
            "ai_review_artifact_number_input"
        ] = int(
            st.session_state.get("ai_review_selected_id", 1)
        )

    artifact_id = st.number_input(
        "Extraction artifact ID",
        min_value=1,
        step=1,
        key="ai_review_artifact_number_input",
    )

    if st.button(
        "Load extraction",
        key="load_ai_extraction",
    ):
        response = api_request(
            "GET",
            f"/ai/extractions/{int(artifact_id)}",
        )

        if response.status_code == 200:
            st.session_state.ai_review_artifact = (
                response.json()
            )
        else:
            st.session_state.pop("ai_review_artifact", None)
            display_api_error(response)

    # SECTION 3: Display and review extracted credentials
    artifact = st.session_state.get("ai_review_artifact")

    if not artifact:
        st.info("Load an extraction to begin reviewing.")
        return

    loaded_id = artifact["artifact_id"]
    version = artifact["version"]
    status = artifact["status"]
    payload = artifact["extraction"]

    st.write(f"**Artifact:** {loaded_id}")
    st.write(f"**Status:** {status}")
    st.write(f"**Version:** {version}")

    message = st.session_state.pop(
        "ai_review_save_message", None
    )

    if message:
        st.success(message)


    st.divider()
    st.markdown("### Final Approval")

    if status == "APPROVED":
        st.success(
            "This AI extraction has been approved "
            "and its accepted records have been saved."
        )

    elif status in ("REVIEW_REQUIRED", "IN_REVIEW"):
        reviews = payload.get("_candidate_reviews", {})

        all_records = [
            f"{collection}:{index}"
            for collection in COLLECTIONS
            for index, _ in enumerate(
                payload.get(collection, [])
            )
        ]

        missing_reviews = [
            key
            for key in all_records
            if reviews.get(key, {}).get("decision")
            not in ("ACCEPT", "EDIT", "REJECT")
        ]

        if missing_reviews:
            st.warning(
                f"{len(missing_reviews)} records still require "
                "a review decision before final approval."
            )
        else:
            confirm = st.checkbox(
                "I confirm that I have reviewed all "
                "extracted academic credentials.",
                key=f"approval_confirm_{loaded_id}_{version}",
            )

            if st.button(
                "Approve and Save Academic Records",
                type="primary",
                disabled=not confirm,
                key=f"approve_{loaded_id}_{version}",
            ):
                try:
                    response = api_request(
                        "POST",
                        f"/ai/extractions/{loaded_id}/approve",
                        json={
                            "expected_version": version,
                            "confirm": True,
                        },
                    )

                    if response.status_code == 200:
                        result = response.json()

                        st.session_state[
                            "approval_success"
                        ] = result

                        refreshed = api_request(
                            "GET",
                            f"/ai/extractions/{loaded_id}",
                        )

                        if refreshed.status_code == 200:
                            st.session_state[
                                "ai_review_artifact"
                            ] = refreshed.json()
                            st.rerun()
                        else:
                            display_api_error(refreshed)

                    else:
                        display_api_error(response)

                except requests.RequestException as exc:
                    st.error(f"Approval request failed: {exc}")

    approval_result = st.session_state.get(
        "approval_success"
    )

    if (
        approval_result
        and approval_result["artifact_id"] == loaded_id
    ):
        st.write("**Official records created:**")
        st.json(approval_result["created_records"])

    if status not in ("REVIEW_REQUIRED", "IN_REVIEW"):
        st.warning("This extraction is no longer editable.")
        return

    saved_reviews = payload.get("_candidate_reviews", {})

    with st.form(f"ai_review_form_{loaded_id}_{version}"):
        selected_reviews = []

        for collection, heading in COLLECTIONS.items():
            records = payload.get(collection, [])
            st.markdown(f"### {heading}")

            if not records:
                st.caption("No records extracted.")
                continue

            for index, record in enumerate(records):
                key = f"{collection}:{index}"
                saved = saved_reviews.get(key, {})

                with st.expander(
                    f"{heading} #{index + 1}",
                    expanded=False,
                ):
                    current_decision = saved.get(
                        "decision", "NOT_REVIEWED"
                    )

                    # Preserve the original AI extraction.
                    original_record = deepcopy(record)
                    reviewed_record = deepcopy(record)

                    # Show saved candidate corrections.
                    if current_decision == "EDIT":
                        reviewed_record.update(
                            saved.get("corrected_data") or {}
                        )

                        st.success(
                            "Candidate correction saved."
                        )

                        st.markdown(
                            "**Corrected record (reviewed draft)**"
                        )
                        st.json(reviewed_record)

                        st.markdown(
                            "**Original AI extraction**"
                        )
                        st.json(original_record)

                    elif current_decision == "ACCEPT":
                        st.success("AI extraction accepted.")
                        st.json(original_record)

                    elif current_decision == "REJECT":
                        st.warning(
                            "Record rejected by the candidate."
                        )
                        st.json(original_record)

                    else:
                        st.info(
                            "This record has not been reviewed yet."
                        )
                        st.json(original_record)

                    # Controls must be outside the decision branches.
                    decision = st.selectbox(
                        "Review decision",
                        options=DECISIONS,
                        index=DECISIONS.index(current_decision),
                        key=f"decision_{loaded_id}_{version}_{key}",
                    )

                    corrections_text = st.text_area(
                        "Corrections (JSON, for EDIT only)",
                        value=json.dumps(
                            saved.get("corrected_data") or {},
                            ensure_ascii=False,
                            indent=2,
                        ),
                        key=f"corrections_{loaded_id}_{version}_{key}",
                        help=(
                            'Example: {"publication_year": 2024}. '
                            "Do not edit evidence."
                        ),
                    )

                    comment = st.text_input(
                        "Review comment (optional)",
                        max_chars=2000,
                        key=f"comment_{loaded_id}_{version}_{key}",
                    )

                    selected_reviews.append(
                        (
                            collection,
                            index,
                            decision,
                            corrections_text,
                            comment,
                        )
                    )

        submitted = st.form_submit_button(
            "Save review decisions",
            type="primary",
        )

    if not submitted:
        return

    reviews = []

    for collection, index, decision, corrections_text, comment in selected_reviews:
        if decision == "NOT_REVIEWED":
            continue

        item = {
            "collection": collection,
            "record_index": index,
            "decision": decision,
            "comment": comment or None,
        }

        if decision == "EDIT":
            try:
                corrections = json.loads(corrections_text)
            except json.JSONDecodeError:
                st.error(
                    f"Invalid JSON in {collection} #{index + 1}"
                )
                return

            if not isinstance(corrections, dict) or not corrections:
                st.error(
                    f"EDIT requires a JSON object with corrections "
                    f"for {collection} #{index + 1}"
                )
                return

            item["corrected_data"] = corrections

        reviews.append(item)

    if not reviews:
        st.warning("Select at least one review decision.")
        return

    response = api_request(
        "PATCH",
        f"/ai/extractions/{loaded_id}/review",
        json={
            "expected_version": version,
            "reviews": reviews,
        },
    )

    if response.status_code == 200:
        refreshed = api_request(
            "GET",
            f"/ai/extractions/{loaded_id}",
        )

        if refreshed.status_code == 200:
            st.session_state["ai_review_artifact"] = refreshed.json()
            st.session_state["ai_review_save_message"] = (
                "Review decisions saved successfully."
            )
            st.rerun()
        else:
            display_api_error(refreshed)

    elif response.status_code == 409:
        st.warning(
            "The extraction has changed. "
            "Click Load extraction and try again."
        )
    else:
        st.error(
            f"Review save failed: HTTP {response.status_code}"
        )
        st.code(response.text, language="json")
