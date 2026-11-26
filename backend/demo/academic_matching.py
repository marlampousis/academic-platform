import requests
import streamlit as st


FINDING_LABELS = {
    "SUPPORTED": "Supported",
    "PARTIALLY_SUPPORTED": "Partially supported",
    "UNSUPPORTED": "Unsupported",
    "INSUFFICIENT_EVIDENCE": "Insufficient evidence",
}


def display_matching_report(
    report,
    requirements=None,
    evidence_details=None,
):
    st.divider()
    st.subheader("Academic Matching Report")
    st.write(f"**Application:** #{report['application_id']}")
    st.write(f"**Academic position:** #{report['position_id']}")

    requirement_lookup = {
        item["requirement_id"]: item
        for item in (requirements or {}).get("requirements", [])
    }

    for match in report.get("matches", []):
        requirement_id = match.get("requirement_id", "Unknown requirement")
        finding = match.get("finding", "INSUFFICIENT_EVIDENCE")
        requirement = requirement_lookup.get(requirement_id, {})
        label = FINDING_LABELS.get(finding, finding)

        with st.expander(f"{requirement_id} | {label}", expanded=True):
            if requirement:
                st.write("**Position requirement:**", requirement.get("description", ""))
                st.write("**Priority:**", requirement.get("priority", "Unknown"))
                st.write("**Category:**", requirement.get("category", "Unknown"))
                st.write("**Original source excerpt:**", requirement.get("source_excerpt", ""))
            else:
                st.caption("Original requirement text available in saved reports.")

            st.write("**AI finding:**", finding)
            st.write("**Explanation:**", match.get("explanation", ""))

            evidence = match.get("evidence", [])

            # Map verified database records by requirement and ID.
            evidence_lookup = {}

            if evidence_details:
                for resolved_match in evidence_details.get(
                    "matches", []
                ):
                    if (
                        resolved_match.get("requirement_id")
                        == requirement_id
                    ):
                        for record in resolved_match.get(
                            "evidence", []
                        ):
                            key = (
                                record["collection"],
                                record["record_id"],
                            )
                            evidence_lookup[key] = record

            if evidence:
                st.write("**Cited academic records:**")
                st.caption(
                    "Evidence details reflect current database records. "
                    "The saved AI assessment reflects the original matching run."
                )

                for item in evidence:
                    collection = item["collection"]
                    record_id = item["record_id"]

                    resolved = evidence_lookup.get(
                        (collection, record_id)
                    )

                    if resolved is None:
                        st.write(
                            f"- {collection} / Record #{record_id}"
                        )
                        continue

                    if not resolved.get("available"):
                        st.warning(
                            f"{collection} / Record #{record_id}: "
                            "No longer available in the current database."
                        )
                        continue

                    details = resolved.get("details") or {}

                    title = resolved.get("title") or (
                        f"Record #{record_id}"
                    )

                    st.write(f"**{title}**")
                    st.caption(
                        f"{collection} · Record #{record_id}"
                    )

                    institution = details.get(
                        "institution_name"
                    )

                    if institution:
                        st.write(
                            f"Institution: {institution}"
                        )

                    if collection == "degrees":
                        st.write(
                            f"Degree type: "
                            f"{details.get('degree_type', 'N/A')}"
                        )

                    if collection == "publications":
                        year = details.get("publication_year")
                        if year:
                            st.write(
                                f"Publication year: {year}"
                            )

                    if collection == "research_projects":
                        role = details.get("role")
                        if role:
                            st.write(f"Role: {role}")

                    if collection == "teaching_experience":
                        role = details.get("teaching_role")
                        if role:
                            st.write(f"Teaching role: {role}")

            else:
                st.info("No academic records cited.")

            uncertainty = match.get("uncertainty")
            if uncertainty:
                st.warning(f"Uncertainty: {uncertainty}")

    st.divider()
    st.write("**AI Summary**")
    st.write(report.get("summary", ""))
    if report.get("requires_human_review"):
        st.warning("Human review is required before any formal evaluation or decision.")
    else:
        st.error("Invalid report: human review was not required.")


def candidate_academic_matching_page(api_request, display_api_error):
    st.subheader("AI Academic Matching")
    st.info(
        "This is a provisional AI-generated assessment. "
        "It is not an eligibility decision. Human review is required."
    )

    try:
        response = api_request("GET", "/applications/me")
    except requests.RequestException:
        st.error("Cannot connect to FastAPI.")
        return

    if response.status_code != 200:
        display_api_error(response)
        return

    applications = [
        app for app in response.json() if app.get("status") == "DRAFT"
    ]
    if not applications:
        st.info("No draft applications available.")
        return

    options = {
        app["id"]: f"Application #{app['id']} | Position #{app['position_id']}"
        for app in applications
    }
    application_id = st.selectbox(
        "Select application",
        options=list(options),
        format_func=lambda value: options[value],
        key="academic_matching_application",
    )

    if st.session_state.get("matching_result_application") != application_id:
        st.session_state.pop("matching_result", None)
        st.session_state.pop("matching_requirements", None)
        st.session_state["matching_result_application"] = application_id

    st.divider()
    st.write("### Generate New Report")
    if st.button(
        "Generate Academic Matching Report",
        type="primary",
        key="generate_academic_matching",
    ):
        try:
            with st.spinner("Generating AI assessment..."):
                result = api_request(
                    "POST",
                    f"/ai/applications/{application_id}/matching-drafts",
                    timeout=180,
                )
            if result.status_code == 200:
                report = result.json()
                if report.get("application_id") != application_id:
                    st.error("Unexpected application in API response.")
                    st.session_state.pop("matching_result", None)
                    st.session_state.pop("matching_requirements", None)
                else:
                    st.session_state["matching_result"] = report
                    st.session_state.pop("matching_requirements", None)
                    st.success("New matching report generated.")
            else:
                st.session_state.pop("matching_result", None)
                st.session_state.pop("matching_requirements", None)
                display_api_error(result)
        except requests.RequestException:
            st.session_state.pop("matching_result", None)
            st.session_state.pop("matching_requirements", None)
            st.error("Matching service is unavailable.")

    st.divider()
    st.write("### Saved Matching Reports")
    try:
        saved_response = api_request(
            "GET", f"/ai/applications/{application_id}/matching-artifacts"
        )
    except requests.RequestException:
        st.error("Cannot load saved matching reports.")
        return

    if saved_response.status_code != 200:
        display_api_error(saved_response)
        return

    saved_reports = saved_response.json()
    if saved_reports:
        report_options = {
            item["artifact_id"]: (
                f"Artifact #{item['artifact_id']} | {item['status']} "
                f"| {item.get('created_at', '')}"
            )
            for item in saved_reports
        }
        selected_artifact = st.selectbox(
            "Select saved report",
            options=list(report_options),
            format_func=lambda value: report_options[value],
            key=f"saved_matching_artifact_{application_id}",
        )
        if st.button(
            "Open Saved Report",
            key=f"open_saved_matching_{application_id}",
        ):  
            try:
                with st.spinner("Loading saved report..."):
                    saved = api_request(
                        "GET", f"/ai/matching-artifacts/{selected_artifact}"
                    )
                if saved.status_code == 200:
                    payload = saved.json()
                    report = payload["matching_draft"]
                    if (
                        payload.get("artifact_id") != selected_artifact
                        or report.get("application_id") != application_id
                    ):
                        st.error("Saved report identity mismatch.")
                        st.session_state.pop("matching_result", None)
                        st.session_state.pop("matching_requirements", None)
                    else:
                        st.session_state["matching_result"] = report
                        st.session_state["matching_requirements"] = payload[
                            "position_requirements"
                        ]
                        
                        # Fetch current PostgreSQL evidence.
                        # This endpoint does not invoke Gemini.
                        st.session_state.pop(
                            "matching_evidence_details", None
                        )

                        evidence_response = api_request(
                            "GET",
                            (
                                f"/ai/matching-artifacts/"
                                f"{selected_artifact}/evidence"
                            ),
                        )

                        if evidence_response.status_code == 200:
                            evidence_payload = (
                                evidence_response.json()
                            )

                            if (
                                evidence_payload.get("artifact_id")
                                == selected_artifact
                                and evidence_payload.get("application_id")
                                == application_id
                                and evidence_payload.get("profile_id")
                                == report.get("profile_id")
                            ):
                                st.session_state[
                                    "matching_evidence_details"
                                ] = evidence_payload
                            else:
                                st.warning(
                                    "Evidence identity mismatch. "
                                    "Current evidence details were not shown."
                                )
                        else:
                            st.warning(
                                "Saved report loaded, but current "
                                "academic evidence details are unavailable."
                            )
                        st.success(f"Loaded saved artifact #{selected_artifact}.")
                else:
                    st.session_state.pop("matching_result", None)
                    st.session_state.pop("matching_requirements", None)
                    display_api_error(saved)
            except (requests.RequestException, KeyError, TypeError):
                st.session_state.pop("matching_result", None)
                st.session_state.pop("matching_requirements", None)
                st.error("Could not load the saved report.")
    else:
        st.info("No saved reports exist for this application.")

    report = st.session_state.get("matching_result")
    if report:
        display_matching_report(
            report,
            requirements=st.session_state.get(
                "matching_requirements"
            ),
            evidence_details=st.session_state.get(
                "matching_evidence_details"
            ),
        )
