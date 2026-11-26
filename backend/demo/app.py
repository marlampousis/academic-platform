
import requests
import streamlit as st

from ai_review import candidate_ai_review_page
from academic_matching import candidate_academic_matching_page

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Academic Credentials Platform",
    page_icon="🎓",
    layout="wide",
)

def api_request(method, endpoint, **kwargs):
    headers = {}

    if st.session_state.get("token"):
        headers["Authorization"] = (
            f"Bearer {st.session_state.token}"
        )

    timeout = kwargs.pop("timeout", 15)

    return requests.request(
        method,
        f"{API_URL}{endpoint}",
        headers=headers,
        timeout=timeout,
        **kwargs,
    )

def display_api_error(response):
    if response.status_code == 401:
        st.error("Session expired. Please log in again.")
    elif response.status_code == 403:
        st.error("You do not have permission to access this.")
    else:
        st.error(
            f"API error {response.status_code}: "
            f"{response.text}"
        )


def display_records(records, empty_message):
    if records:
        st.dataframe(
            records,
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(empty_message)


def get_role(user):
    role = user.get("role")

    if isinstance(role, dict):
        return str(role.get("code", "")).upper()

    if isinstance(role, str):
        return role.upper()

    return str(user.get("role_code", "")).upper()


def login_page():
    st.subheader("Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button("Login")

    if submitted:
        try:
            response = api_request(
                "POST",
                "/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
            )

            if response.status_code == 200:
                st.session_state.token = (
                    response.json()["access_token"]
                )
                st.rerun()
            else:
                display_api_error(response)

        except requests.RequestException:
            st.error("Cannot connect to FastAPI.")

def candidate_dashboard():
    st.header("Candidate Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs([
        "My Applications",
        "Create Application",
        "AI CV Review",
        "AI Academic Matching",
    ])

    with tab1:
        st.subheader("My Applications")

        response = api_request(
            "GET",
            "/applications/me",
        )

        if response.status_code == 200:
            applications = response.json()

            display_records(
                applications,
                "You have no applications.",
            )

            drafts = [
                application
                for application in applications
                if application["status"] == "DRAFT"
            ]

            if drafts:
                st.subheader("Submit Draft Application")

                draft_options = {
                    (
                        f"Application {app['id']} "
                        f"(Position {app['position_id']})"
                    ): app["id"]
                    for app in drafts
                }

                selected_draft = st.selectbox(
                    "Select a draft application",
                    options=list(draft_options.keys()),
                )

                application_id = draft_options[selected_draft]

                if st.button("Validate Application"):
                    validation = api_request(
                        "GET",
                        f"/applications/{application_id}/validation",
                    )

                    if validation.status_code == 200:
                        result = validation.json()

                        if result.get("can_submit"):
                            st.success(
                                "Application is ready for submission."
                            )
                        else:
                            st.warning("Application cannot be submitted.")

                            for error in result.get("errors", []):
                                st.error(error)

                            missing = result.get("missing_required_documents", [])

                            if missing:
                                st.subheader("Missing Required Documents")

                                for document in missing:
                                    st.write(
                                        f"- {document.get('document_type_name', 'Unknown document')}"
                                    )

                            with st.expander("Full Validation Details"):
                                st.json(result)
                    else:
                        display_api_error(validation)

                if st.button("Submit Application"):
                    validation = api_request(
                        "GET",
                        f"/applications/{application_id}/validation",
                    )

                    if validation.status_code != 200:
                        display_api_error(validation)

                    elif not validation.json().get("can_submit"):
                        st.warning(
                            "Application cannot be submitted."
                        )
                        st.json(validation.json())

                    else:
                        submitted = api_request(
                            "POST",
                            f"/applications/{application_id}/submit",
                        )

                        if submitted.status_code == 200:
                            st.success(
                                "Application submitted successfully."
                            )
                            st.rerun()
                        else:
                            display_api_error(submitted)

        else:
            display_api_error(response)

    
    with tab2:
        st.subheader("Create New Application")

        try:
            positions_response = api_request(
                "GET",
                "/positions/",
            )

            if positions_response.status_code == 200:
                positions = positions_response.json()

                if not positions:
                    st.info("No academic positions available.")

                else:
                    position_options = {
                        position["id"]: (
                            f"{position['title']} "
                            f"(ID: {position['id']})"
                        )
                        for position in positions
                    }

                    selected_id = st.selectbox(
                        "Academic Position",
                        options=list(position_options.keys()),
                        format_func=lambda position_id:
                            position_options[position_id],
                    )

                    selected_position = next(
                        position
                        for position in positions
                        if position["id"] == selected_id
                    )

                    st.subheader("Position Details")
                    st.write(
                        "**Title:**",
                        selected_position.get("title"),
                    )
                    st.write(
                        "**Field of study:**",
                        selected_position.get("field_of_study"),
                    )
                    st.write(
                        "**Application deadline:**",
                        selected_position.get("application_deadline"),
                    )
                    st.write(
                        "**Available positions:**",
                        selected_position.get("positions_available"),
                    )

                    existing_ids = {
                        item["position_id"]
                        for item in applications
                    } if "applications" in locals() else set()

                    if selected_id in existing_ids:
                        st.warning(
                            "You already have an application "
                            "for this academic position."
                        )

                    elif st.button("Create Draft Application"):
                        create_response = api_request(
                            "POST",
                            "/applications/",
                            json={
                                "position_id": selected_id,
                            },
                        )

                        if create_response.status_code == 201:
                            st.success(
                                "Draft application created successfully."
                            )
                            st.rerun()
                        else:
                            display_api_error(create_response)

            else:
                display_api_error(positions_response)

        except requests.RequestException:
            st.error("Cannot load academic positions.")

    with tab3:
        candidate_ai_review_page(
            api_request=api_request,
            display_api_error=display_api_error,
        )

    with tab4:
        candidate_academic_matching_page(
            api_request=api_request,
            display_api_error=display_api_error,
        )

def committee_management():
    st.divider()
    st.subheader("Committee Management")

    committees_response = api_request(
        "GET", "/evaluation-committees/"
    )
    positions_response = api_request(
        "GET", "/positions/"
    )

    if committees_response.status_code != 200:
        display_api_error(committees_response)
        return

    if positions_response.status_code != 200:
        display_api_error(positions_response)
        return

    committees = committees_response.json()
    positions = positions_response.json()

    create_tab, configure_tab = st.tabs([
        "Create Committee",
        "Configure Committee",
    ])

    # =========================================
    # CREATE COMMITTEE
    # =========================================
    with create_tab:
        existing_position_ids = {
            item["position_id"]
            for item in committees
        }

        available_positions = [
            position for position in positions
            if position["id"] not in existing_position_ids
        ]

        if not available_positions:
            st.info(
                "Every position already has a committee."
            )
        else:
            position_options = {
                p["id"]: f"{p['title']} (ID: {p['id']})"
                for p in available_positions
            }

            with st.form("create_committee_form"):
                position_id = st.selectbox(
                    "Academic Position",
                    options=list(position_options),
                    format_func=lambda pid:
                        position_options[pid],
                    key="committee_create_position",
                )

                committee_name = st.text_input(
                    "Committee Name",
                    value="S01 E2E Evaluation Committee",
                )

                description = st.text_area(
                    "Committee Description",
                    value=(
                        "Development-only evaluation committee "
                        "for S01 end-to-end testing."
                    ),
                )

                create = st.form_submit_button(
                    "Create Committee",
                    type="primary",
                )

            if create:
                if len(committee_name.strip()) < 3:
                    st.error(
                        "Committee name must contain "
                        "at least 3 characters."
                    )
                else:
                    result = api_request(
                        "POST",
                        "/evaluation-committees/",
                        json={
                            "position_id": int(position_id),
                            "name": committee_name.strip(),
                            "description": (
                                description.strip() or None
                            ),
                        },
                    )

                    if result.status_code == 201:
                        created = result.json()
                        st.session_state.created_committee_id = (
                            created["id"]
                        )
                        st.success(
                            f"Committee {created['id']} created."
                        )
                        st.rerun()
                    else:
                        display_api_error(result)

    # =========================================
    # CONFIGURE AN EXISTING COMMITTEE
    # =========================================
    with configure_tab:
        if not committees:
            st.info("Create a committee first.")
            return

        committee_options = {
            item["id"]: (
                f"{item['name']} "
                f"(ID: {item['id']}) - {item['status']}"
            )
            for item in committees
        }

        committee_ids = list(committee_options)
        created_id = st.session_state.get(
            "created_committee_id"
        )

        default_index = (
            committee_ids.index(created_id)
            if created_id in committee_ids
            else 0
        )

        committee_id = st.selectbox(
            "Select Committee",
            options=committee_ids,
            index=default_index,
            format_func=lambda cid:
                committee_options[cid],
            key="committee_configure_select",
        )

        selected_committee = next(
            item for item in committees
            if item["id"] == committee_id
        )

        committee_status = selected_committee["status"]

        st.write(
            "**Academic Position:**",
            selected_committee["position_id"],
        )
        st.write(
            "**Committee Status:**",
            committee_status,
        )

        members_tab, criteria_tab, assignments_tab = st.tabs([
            "Members",
            "Evaluation Criteria",
            "Application Assignment",
        ])

        # =========================================
        # COMMITTEE MEMBERS
        # =========================================
        with members_tab:
            st.subheader("Committee Members")

            members_url = (
                f"/evaluation-committees/"
                f"{committee_id}/members"
            )

            members_response = api_request(
                "GET", members_url
            )

            if members_response.status_code != 200:
                display_api_error(members_response)
            else:
                members = members_response.json()

                display_records(
                    members,
                    "No members assigned yet.",
                )

                if committee_status in ("DRAFT", "ACTIVE"):
                    existing_user_ids = {
                        m["user_id"] for m in members
                    }

                    with st.form(
                        f"add_member_form_{committee_id}"
                    ):
                        user_id = st.number_input(
                            "Reviewer User ID",
                            min_value=1,
                            step=1,
                        )

                        member_role = st.selectbox(
                            "Role in Committee",
                            ["CHAIR", "MEMBER", "SECRETARY"],
                        )

                        add_member = st.form_submit_button(
                            "Add Member"
                        )

                    if add_member:
                        if int(user_id) in existing_user_ids:
                            st.warning(
                                "This user is already a "
                                "committee member."
                            )
                        else:
                            result = api_request(
                                "POST",
                                members_url,
                                json={
                                    "user_id": int(user_id),
                                    "role_in_committee": member_role,
                                },
                            )

                            if result.status_code == 201:
                                st.success(
                                    "Committee member added."
                                )
                                st.rerun()
                            else:
                                display_api_error(result)

                else:
                    st.info(
                        "Membership cannot be changed "
                        "in this committee state."
                    )

        
        # =========================================
        # EVALUATION CRITERIA
        # =========================================
        with criteria_tab:
            st.subheader("Evaluation Criteria")

            criteria_url = (
                f"/evaluation-committees/"
                f"{committee_id}/criteria"
            )

            criteria_response = api_request(
                "GET", criteria_url
            )

            if criteria_response.status_code != 200:
                display_api_error(criteria_response)
            else:
                criteria = criteria_response.json()

                display_records(
                    criteria,
                    "No criteria configured yet.",
                )

                total_weight = sum(
                    float(c["weight"])
                    for c in criteria
                    if c.get("is_active", False)
                )

                st.metric(
                    "Total Active Weight",
                    f"{total_weight:.2f}%",
                )

                if committee_status == "DRAFT":
                    with st.form(
                        f"add_criterion_{committee_id}"
                    ):
                        code = st.text_input(
                            "Criterion Code",
                            placeholder="RESEARCH_EXPERIENCE",
                        )

                        name = st.text_input(
                            "Criterion Name",
                            placeholder="Research Experience",
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            weight = st.number_input(
                                "Weight (%)",
                                min_value=0.01,
                                max_value=100.0,
                                value=10.0,
                                step=0.5,
                            )

                        with col2:
                            max_score = st.number_input(
                                "Maximum Score",
                                min_value=0.01,
                                value=10.0,
                                step=0.5,
                            )

                        display_order = st.number_input(
                            "Display Order",
                            min_value=0,
                            value=len(criteria) + 1,
                            step=1,
                        )

                        add_criterion = st.form_submit_button(
                            "Add Criterion"
                        )

                    if add_criterion:
                        if len(code.strip()) < 2:
                            st.error(
                                "Criterion code is too short."
                            )

                        elif len(name.strip()) < 3:
                            st.error(
                                "Criterion name is too short."
                            )

                        elif total_weight + weight > 100.0001:
                            st.error(
                                "Total active weight "
                                "cannot exceed 100%."
                            )

                        else:
                            result = api_request(
                                "POST",
                                criteria_url,
                                json={
                                    "code": code.strip(),
                                    "name": name.strip(),
                                    "weight": weight,
                                    "max_score": max_score,
                                    "display_order": int(
                                        display_order
                                    ),
                                    "is_active": True,
                                },
                            )

                            if result.status_code == 201:
                                st.success(
                                    "Evaluation criterion added."
                                )
                                st.rerun()
                            else:
                                display_api_error(result)

                    st.divider()
                    st.subheader("Activate Committee")

                    weight_complete = (
                        abs(total_weight - 100.0) < 0.0001
                    )

                    members_check = api_request(
                        "GET",
                        (
                            f"/evaluation-committees/"
                            f"{committee_id}/members"
                        ),
                    )

                    active_members = (
                        [
                            m for m in members_check.json()
                            if m["is_active"]
                        ]
                        if members_check.status_code == 200
                        else []
                    )

                    has_chair = any(
                        m["role_in_committee"] == "CHAIR"
                        for m in active_members
                    )

                    ready = (
                        weight_complete
                        and len(active_members) >= 2
                        and has_chair
                    )

                    if not weight_complete:
                        st.warning(
                            "Criteria weights must total 100%."
                        )

                    if len(active_members) < 2:
                        st.warning(
                            "Add at least two active committee members."
                        )

                    if not has_chair:
                        st.warning(
                            "Assign an active committee chair."
                        )

                    if st.button(
                        "Activate Committee",
                        disabled=not ready,
                        type="primary",
                        key=f"activate_committee_{committee_id}",
                    ):
                        result = api_request(
                            "PUT",
                            (
                                f"/evaluation-committees/"
                                f"{committee_id}"
                            ),
                            json={"status": "ACTIVE"},
                        )

                        if result.status_code == 200:
                            st.success("Committee activated.")
                            st.rerun()
                        else:
                            display_api_error(result)

                else:
                    st.info(
                        "Evaluation criteria can only be "
                        "modified while the committee is DRAFT."
                    )

        
        # =========================================
        # APPLICATION ASSIGNMENT
        # =========================================
        with assignments_tab:
            st.subheader("Committee Applications")

            base_url = (
                f"/evaluation-committees/{committee_id}"
            )

            assignments_response = api_request(
                "GET", f"{base_url}/applications"
            )

            if assignments_response.status_code != 200:
                display_api_error(assignments_response)
            else:
                assignments = assignments_response.json()

                display_records(
                    assignments,
                    "No applications assigned yet.",
                )

                if committee_status == "ACTIVE":
                    position_id = selected_committee[
                        "position_id"
                    ]

                    eligible_response = api_request(
                        "GET",
                        (
                            f"/admin/positions/"
                            f"{position_id}/applications"
                        ),
                        params={"status": "ELIGIBLE"},
                    )

                    if eligible_response.status_code != 200:
                        display_api_error(eligible_response)
                    else:
                        assigned_application_ids = {
                            item["application_id"]
                            for item in assignments
                        }

                        eligible = [
                            item
                            for item in eligible_response.json()
                            if item["id"] not in assigned_application_ids
                        ]

                        if eligible:
                            options = {
                                item["id"]: (
                                    f"Application {item['id']}"
                                )
                                for item in eligible
                            }

                            with st.form(
                                f"assign_application_{committee_id}"
                            ):
                                application_id = st.selectbox(
                                    "Eligible Application",
                                    options=list(options),
                                    format_func=lambda aid:
                                        options[aid],
                                )

                                notes = st.text_area(
                                    "Assignment Notes",
                                    value="S01 E2E evaluation",
                                )

                                assign = st.form_submit_button(
                                    "Assign Application"
                                )

                            if assign:
                                result = api_request(
                                    "POST",
                                    f"{base_url}/applications",
                                    json={
                                        "application_id": int(
                                            application_id
                                        ),
                                        "notes": notes or None,
                                    },
                                )

                                if result.status_code == 201:
                                    st.success(
                                        "Application assigned."
                                    )
                                    st.rerun()
                                else:
                                    display_api_error(result)
                        else:
                            st.info(
                                "No unassigned eligible "
                                "applications are available."
                            )

                    st.divider()
                    st.subheader("Start Evaluation")

                    pending_assignments = [
                        item for item in assignments
                        if item["status"] == "ASSIGNED"
                    ]

                    if pending_assignments:
                        assignment_options = {
                            item["id"]: (
                                f"Assignment {item['id']} "
                                f"(Application "
                                f"{item['application_id']})"
                            )
                            for item in pending_assignments
                        }

                        selected_assignment_id = st.selectbox(
                            "Assignment",
                            options=list(assignment_options),
                            format_func=lambda aid:
                                assignment_options[aid],
                            key=f"start_assignment_{committee_id}",
                        )

                        if st.button(
                            "Start Evaluation",
                            type="primary",
                            key=f"start_evaluation_{committee_id}",
                        ):
                            result = api_request(
                                "PUT",
                                (
                                    f"{base_url}/applications/"
                                    f"{selected_assignment_id}"
                                ),
                                json={
                                    "status": "IN_EVALUATION"
                                },
                            )

                            if result.status_code == 200:
                                st.success(
                                    "Evaluation started."
                                )
                                st.rerun()
                            else:
                                display_api_error(result)
                    else:
                        st.info(
                            "No assignments are waiting "
                            "to start evaluation."
                        )

                else:
                    st.info(
                        "Activate the committee before "
                        "assigning applications."
                    )

def admin_dashboard():
    st.header("Super Admin Dashboard")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Application Reviews",
        "Evaluation Committees",
        "Ranking & Results",
        "Create Academic Position",
    ])

    # --------------------------------------------------
    # TAB 1: APPLICATION REVIEWS
    # --------------------------------------------------
    with tab1:
        st.subheader("Application Eligibility Review")

        positions_response = api_request(
            "GET",
            "/positions/",
        )

        if positions_response.status_code != 200:
            display_api_error(positions_response)

        else:
            positions = positions_response.json()

            if not positions:
                st.info("No academic positions found.")

            else:
                position_options = {
                    position["id"]: (
                        f"{position['title']} "
                        f"(ID: {position['id']})"
                    )
                    for position in positions
                }

                position_id = st.selectbox(
                    "Academic Position",
                    options=list(position_options.keys()),
                    format_func=lambda pid: position_options[pid],
                    key="admin_review_position",
                )

                status_filter = st.selectbox(
                    "Filter Applications",
                    [
                        "ALL",
                        "DRAFT",
                        "SUBMITTED",
                        "UNDER_REVIEW",
                        "ELIGIBLE",
                        "REJECTED",
                    ],
                    key="admin_review_filter",
                )

                params = {}

                if status_filter != "ALL":
                    params["status"] = status_filter

                applications_response = api_request(
                    "GET",
                    f"/admin/positions/{position_id}/applications",
                    params=params,
                )

                if applications_response.status_code != 200:
                    display_api_error(applications_response)

                else:
                    applications = applications_response.json()

                    display_records(
                        applications,
                        "No applications match these filters.",
                    )

                    if applications:
                        application_options = {
                            application["id"]: (
                                f"Application {application['id']} "
                                f"- {application['status']}"
                            )
                            for application in applications
                        }

                        application_id = st.selectbox(
                            "Select Application",
                            options=list(application_options.keys()),
                            format_func=lambda aid:
                                application_options[aid],
                            key="admin_selected_application",
                        )

                        details = api_request(
                            "GET",
                            f"/admin/applications/{application_id}",
                        )

                        if details.status_code != 200:
                            display_api_error(details)

                        else:
                            application = details.json()
                            current_status = application["status"]

                            st.subheader("Application Details")

                            col1, col2, col3 = st.columns(3)

                            col1.metric(
                                "Application ID",
                                application["id"],
                            )

                            col2.metric(
                                "Candidate User ID",
                                application["user_id"],
                            )

                            col3.metric(
                                "Current Status",
                                current_status,
                            )

                            allowed = {
                                "SUBMITTED": ["UNDER_REVIEW"],
                                "UNDER_REVIEW": [
                                    "ELIGIBLE",
                                    "REJECTED",
                                ],
                            }

                            next_statuses = allowed.get(
                                current_status,
                                [],
                            )

                            if next_statuses:
                                st.subheader("Update Review Status")

                                with st.form(
                                    f"review_form_{application_id}"
                                ):
                                    new_status = st.selectbox(
                                        "New Status",
                                        next_statuses,
                                    )

                                    comment = st.text_area(
                                        "Review Comment",
                                        max_chars=1000,
                                    )

                                    confirm = st.form_submit_button(
                                        "Save Review Decision",
                                    )

                                if confirm:
                                    update_response = api_request(
                                        "PATCH",
                                        (
                                            f"/admin/applications/"
                                            f"{application_id}/status"
                                        ),
                                        json={
                                            "status": new_status,
                                            "comment": comment or None,
                                        },
                                    )

                                    if update_response.status_code == 200:
                                        st.success(
                                            "Review status updated."
                                        )
                                        st.rerun()
                                    else:
                                        display_api_error(update_response)

                            else:
                                st.info(
                                    "No review transitions are "
                                    "available for this status."
                                )

    # --------------------------------------------------
    # TAB 2: EVALUATION COMMITTEES
    # --------------------------------------------------
    with tab2:
        st.subheader("Evaluation Committees")

        response = api_request(
            "GET",
            "/evaluation-committees/",
        )

        if response.status_code == 200:
            display_records(
                response.json(),
                "No evaluation committees found.",
            )
        else:
            display_api_error(response)

        committee_management()
    # --------------------------------------------------
    # TAB 3: RANKINGS
    # --------------------------------------------------
    
    with tab3:
        st.subheader("Committee Rankings & Final Decisions")

        committees_response = api_request(
            "GET",
            "/evaluation-committees/",
        )

        if committees_response.status_code != 200:
            display_api_error(committees_response)

        else:
            committees = committees_response.json()

            if not committees:
                st.info("No committees available.")

            else:
                committee_options = {
                    committee["id"]: (
                        f"{committee['name']} "
                        f"(ID: {committee['id']})"
                    )
                    for committee in committees
                }

                committee_id = st.selectbox(
                    "Select Evaluation Committee",
                    options=list(committee_options),
                    format_func=lambda cid: committee_options[cid],
                    key="ranking_committee_select",
                )

                ranking_url = (
                    f"/evaluation-committees/"
                    f"{committee_id}/ranking"
                )

                st.subheader("Existing Ranking")

                ranking_response = api_request(
                    "GET",
                    ranking_url,
                )

                if ranking_response.status_code == 200:
                    ranking_items = ranking_response.json()

                    display_records(
                        ranking_items,
                        "No ranking generated yet.",
                    )

                else:
                    ranking_items = []
                    display_api_error(ranking_response)

                st.divider()
                st.subheader("Generate Ranking")

                st.caption(
                    "Ranking requires submitted reports "
                    "from every active reviewer. "
                    "This action writes results to the database."
                )

                confirm_generation = st.checkbox(
                    "I confirm that the committee "
                    "is ready for ranking.",
                    key=f"confirm_ranking_{committee_id}",
                )

                finalized_results = any(
                    item.get("decision") not in (None, "PENDING")
                    for item in ranking_items
                )

                if finalized_results:
                    st.info(
                        "This committee has finalized decisions. "
                        "Ranking regeneration is locked."
                    )

                if st.button(
                    "Generate / Recalculate Ranking",
                    disabled=(
                        not confirm_generation or finalized_results
                    ),
                    key="generate_ranking_button",
                ):
                    generated = api_request(
                        "POST",
                        f"{ranking_url}/generate",
                    )

                    if generated.status_code == 200:
                        st.success("Ranking generated successfully.")
                        st.rerun()
                    else:
                        display_api_error(generated)

                st.divider()
                st.subheader("Final Decision")

                pending_results = [
                    item
                    for item in ranking_items
                    if item.get("decision") == "PENDING"
                ]

                if not pending_results:
                    st.info(
                        "No applications with pending "
                        "final decisions are available."
                    )

                else:
                    result_options = {
                        item["committee_application_id"]: (
                            f"Application {item['application_id']} "
                            f"| Rank {item['rank_position']} "
                            f"| Score {item['final_score']}"
                        )
                        for item in pending_results
                    }

                    assignment_id = st.selectbox(
                        "Application to Decide",
                        options=list(result_options),
                        format_func=lambda aid: result_options[aid],
                        key="decision_assignment",
                    )

                    with st.form("final_decision_form"):
                        decision = st.selectbox(
                            "Final Decision",
                            [
                                "SELECTED",
                                "NOT_SELECTED",
                                "RESERVE",
                            ],
                        )

                        final_comment = st.text_area(
                            "Decision Justification",
                            max_chars=5000,
                        )

                        confirmed = st.checkbox(
                            "I confirm this final decision."
                        )

                        submit_decision = st.form_submit_button(
                            "Record Final Decision"
                        )

                    if submit_decision:
                        if not confirmed:
                            st.warning(
                                "Please confirm the decision."
                            )

                        else:
                            decision_url = (
                                f"/evaluation-committees/"
                                f"{committee_id}/applications/"
                                f"{assignment_id}/result/decision"
                            )

                            result = api_request(
                                "PUT",
                                decision_url,
                                json={
                                    "decision": decision,
                                    "final_comment": (
                                        final_comment or None
                                    ),
                                },
                            )

                            if result.status_code == 200:
                                st.success(
                                    "Final decision recorded."
                                )
                                st.rerun()
                            else:
                                display_api_error(result)

    # ---------------------------------------------
    # TAB 4: CREATE ACADEMIC POSITION
    # ---------------------------------------------
    with tab4:
        st.subheader("Create Academic Position")

        st.caption(
            "Create a new academic vacancy using "
            "the existing FastAPI backend."
        )

        reference_endpoints = {
            "institutions": "/institutions/",
            "departments": "/departments/",
            "ranks": "/academic-ranks/",
            "employment_types": "/employment-types/",
            "statuses": "/position-statuses/",
        }

        reference_data = {}
        loading_failed = False

        for key, endpoint in reference_endpoints.items():
            try:
                response = api_request("GET", endpoint)

                if response.status_code != 200:
                    st.error(
                        f"Cannot load {key}: "
                        f"HTTP {response.status_code}"
                    )
                    loading_failed = True
                    break

                reference_data[key] = response.json()

            except requests.RequestException as exc:
                st.error(f"Cannot load {key}: {exc}")
                loading_failed = True
                break

        if not loading_failed:
            institutions = reference_data["institutions"]
            departments = reference_data["departments"]
            ranks = reference_data["ranks"]
            employment_types = reference_data["employment_types"]
            statuses = reference_data["statuses"]

            if not all([
                institutions,
                departments,
                ranks,
                employment_types,
                statuses,
            ]):
                st.warning(
                    "Some required reference records are missing."
                )

            else:
                institution_options = {
                    item["id"]: item.get(
                        "name_el",
                        item.get("name_en", str(item["id"]))
                    )
                    for item in institutions
                }

                institution_id = st.selectbox(
                    "Institution",
                    list(institution_options),
                    format_func=lambda value:
                        institution_options[value],
                    key="new_position_institution",
                )

                matching_departments = [
                    item
                    for item in departments
                    if item["institution_id"] == institution_id
                ]

                if not matching_departments:
                    st.warning(
                        "No departments belong to this institution."
                    )

                else:
                    department_options = {
                        item["id"]: item.get(
                            "name_el",
                            item.get("name_en", str(item["id"]))
                        )
                        for item in matching_departments
                    }

                    rank_options = {
                        item["id"]: item["name"]
                        for item in ranks
                    }

                    employment_options = {
                        item["id"]: item["name"]
                        for item in employment_types
                    }

                    status_options = {
                        item["id"]: item["code"]
                        for item in statuses
                    }

                    open_status_id = next(
                        (
                            sid
                            for sid, code in status_options.items()
                            if code == "OPEN"
                        ),
                        None,
                    )

                    with st.form("create_position_form"):
                        title = st.text_input(
                            "Position Title",
                            placeholder=(
                                "Assistant Professor in "
                                "Artificial Intelligence"
                            ),
                        )

                        department_id = st.selectbox(
                            "Department",
                            list(department_options),
                            format_func=lambda value:
                                department_options[value],
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            academic_rank_id = st.selectbox(
                                "Academic Rank",
                                list(rank_options),
                                format_func=lambda value:
                                    rank_options[value],
                            )

                        with col2:
                            employment_type_id = st.selectbox(
                                "Employment Type",
                                list(employment_options),
                                format_func=lambda value:
                                    employment_options[value],
                            )

                        field_of_study = st.text_input(
                            "Field of Study",
                            placeholder="Artificial Intelligence",
                        )

                        description = st.text_area(
                            "Position Description",
                            height=130,
                        )

                        col3, col4 = st.columns(2)

                        with col3:
                            application_start_date = st.date_input(
                                "Application Start Date",
                                value="today",
                            )

                        with col4:
                            application_deadline = st.date_input(
                                "Application Deadline",
                                value="today",
                            )

                        positions_available = st.number_input(
                            "Positions Available",
                            min_value=1,
                            value=1,
                            step=1,
                        )

                        status_id = st.selectbox(
                            "Position Status",
                            list(status_options),
                            index=(
                                list(status_options).index(open_status_id)
                                if open_status_id is not None
                                else 0
                            ),
                            format_func=lambda value:
                                status_options[value],
                        )

                        st.divider()

                        confirmed = st.checkbox(
                            "I confirm that this position "
                            "is ready to be created."
                        )

                        create_position = st.form_submit_button(
                            "Create Academic Position",
                            type="primary",
                        )

                    if create_position:
                        if not confirmed:
                            st.warning(
                                "Please confirm position creation."
                            )

                        elif not title.strip():
                            st.error("Position title is required.")

                        elif not field_of_study.strip():
                            st.error("Field of study is required.")

                        elif not description.strip():
                            st.error("Description is required.")

                        elif application_start_date > application_deadline:
                            st.error(
                                "The application start date "
                                "cannot be after the deadline."
                            )

                        else:
                            payload = {
                                "institution_id": int(institution_id),
                                "department_id": int(department_id),
                                "title": title.strip(),
                                "academic_rank_id": int(academic_rank_id),
                                "field_of_study": field_of_study.strip(),
                                "description": description.strip(),
                                "employment_type_id": int(employment_type_id),
                                "application_start_date": (
                                    application_start_date.isoformat()
                                ),
                                "application_deadline": (
                                    application_deadline.isoformat()
                                ),
                                "positions_available": int(
                                    positions_available
                                ),
                                "position_status_id": int(status_id),
                            }

                            try:
                                result = api_request(
                                    "POST",
                                    "/positions/",
                                    json=payload,
                                )

                                if result.status_code == 201:
                                    created = result.json()

                                    st.success(
                                        "Academic position created!"
                                    )

                                    st.write(
                                        "New Position ID:",
                                        created["id"],
                                    )

                                    st.json(created)

                                else:
                                    display_api_error(result)

                            except requests.RequestException as exc:
                                st.error(
                                    f"Position creation failed: {exc}"
                                )


def reviewer_dashboard():
    st.header("Reviewer Dashboard")

    st.write(
        "Review assigned applications, enter evaluation "
        "scores, and submit your evaluation report."
    )

    committee_id = int(
        st.number_input(
            "Committee ID",
            min_value=1,
            step=1,
            key="reviewer_committee_id",
        )
    )

    if st.button("Load Committee Applications"):
        st.session_state.reviewer_loaded_committee = committee_id

    if st.session_state.get("reviewer_loaded_committee") != committee_id:
        st.info("Load a committee to begin.")
        return

    # 1. Retrieve committee assignments.
    assignments_response = api_request(
        "GET",
        f"/evaluation-committees/{committee_id}/applications",
    )

    if assignments_response.status_code != 200:
        display_api_error(assignments_response)
        return

    assignments = assignments_response.json()

    if not assignments:
        st.info("No applications assigned to this committee.")
        return

    st.subheader("Assigned Applications")

    display_records(
        assignments,
        "No assignments found.",
    )

    # 2. Select an application.
    assignment_options = {
        assignment["id"]: (
            f"Assignment {assignment['id']} | "
            f"Application {assignment['application_id']} | "
            f"{assignment['status']}"
        )
        for assignment in assignments
    }

    assignment_id = st.selectbox(
        "Select Application to Evaluate",
        options=list(assignment_options.keys()),
        format_func=lambda value: assignment_options[value],
        key="reviewer_selected_assignment",
    )

    selected_assignment = next(
        item for item in assignments
        if item["id"] == assignment_id
    )

    if selected_assignment["status"] != "IN_EVALUATION":
        st.warning(
            "This application is not currently IN_EVALUATION."
        )
        return

    base_url = (
        f"/evaluation-committees/{committee_id}"
        f"/applications/{assignment_id}"
    )

    # 3. Load evaluation criteria.
    criteria_response = api_request(
        "GET",
        f"/evaluation-committees/{committee_id}/criteria",
    )

    if criteria_response.status_code != 200:
        display_api_error(criteria_response)
        return

    criteria = [
        criterion
        for criterion in criteria_response.json()
        if criterion.get("is_active", True)
    ]

    if not criteria:
        st.warning("No active evaluation criteria found.")
        return

    # 4. Load existing reviewer scores.
    scores_response = api_request(
        "GET",
        f"{base_url}/scores/me",
    )

    if scores_response.status_code != 200:
        display_api_error(scores_response)
        return

    existing_scores = scores_response.json()

    scored_criterion_ids = {
        score["criterion_id"]
        for score in existing_scores
    }

    # 5. Load existing reviewer report.
    report_response = api_request(
        "GET",
        f"{base_url}/reports/me",
    )

    if report_response.status_code == 200:
        existing_report = report_response.json()

    elif report_response.status_code == 404:
        existing_report = None

    else:
        display_api_error(report_response)
        return

    report_submitted = (
        existing_report is not None
        and existing_report["status"] == "SUBMITTED"
    )

    tab1, tab2 = st.tabs([
        "Evaluation Scores",
        "Evaluation Report",
    ])

    # ---------------------------------------------
    # TAB 1: SCORING
    # ---------------------------------------------
    with tab1:
        st.subheader("Evaluation Criteria")

        display_records(
            criteria,
            "No active criteria available.",
        )

        st.subheader("My Scores")

        display_records(
            existing_scores,
            "You have not submitted any scores.",
        )

        remaining_criteria = [
            criterion
            for criterion in criteria
            if criterion["id"] not in scored_criterion_ids
        ]

        if report_submitted:
            st.success(
                "Report submitted. Evaluation scores are locked."
            )

        elif not remaining_criteria:
            st.success("All active criteria have been scored.")

        else:
            st.subheader("Add Evaluation Score")

            criterion_options = {
                criterion["id"]: (
                    f"{criterion['name']} "
                    f"(Maximum: {criterion['max_score']})"
                )
                for criterion in remaining_criteria
            }

            criterion_id = st.selectbox(
                "Criterion",
                options=list(criterion_options.keys()),
                format_func=lambda value:
                    criterion_options[value],
            )

            selected_criterion = next(
                criterion
                for criterion in remaining_criteria
                if criterion["id"] == criterion_id
            )

            max_score = float(
                selected_criterion["max_score"]
            )

            with st.form(
                f"score_form_{assignment_id}_{criterion_id}"
            ):
                score_value = st.number_input(
                    "Score",
                    min_value=0.0,
                    max_value=max_score,
                    value=0.0,
                    step=0.5,
                )

                score_comment = st.text_area(
                    "Score Justification",
                    max_chars=3000,
                )

                save_score = st.form_submit_button(
                    "Save Evaluation Score"
                )

            if save_score:
                result = api_request(
                    "POST",
                    f"{base_url}/scores",
                    json={
                        "criterion_id": int(criterion_id),
                        "score": score_value,
                        "comment": score_comment or None,
                    },
                )

                if result.status_code == 201:
                    st.success("Evaluation score saved.")
                    st.rerun()
                else:
                    display_api_error(result)

    # ---------------------------------------------
    # TAB 2: EVALUATION REPORT
    # ---------------------------------------------
    with tab2:
        st.subheader("Evaluation Report")

        all_scored = (
            len(scored_criterion_ids) == len(criteria)
            and all(
                criterion["id"] in scored_criterion_ids
                for criterion in criteria
            )
        )

        st.write(
            f"Criteria completed: "
            f"{len(scored_criterion_ids)}/{len(criteria)}"
        )

        if existing_report:
            st.metric(
                "Weighted Evaluation Score",
                existing_report["weighted_score"],
            )

            st.write(
                "**Report Status:**",
                existing_report["status"],
            )

            st.write(
                "**Final Comment:**",
                existing_report.get("final_comment") or "-",
            )

            if report_submitted:
                st.success(
                    "Your evaluation report has been submitted."
                )

            else:
                if st.button(
                    "Submit Final Evaluation Report",
                    type="primary",
                ):
                    submit_response = api_request(
                        "POST",
                        (
                            f"{base_url}/reports/"
                            f"{existing_report['id']}/submit"
                        ),
                    )

                    if submit_response.status_code == 200:
                        st.success(
                            "Evaluation report submitted."
                        )
                        st.rerun()
                    else:
                        display_api_error(submit_response)

        elif not all_scored:
            st.warning(
                "Complete all evaluation criteria "
                "before creating your report."
            )

        else:
            with st.form(
                f"report_form_{assignment_id}"
            ):
                final_comment = st.text_area(
                    "Final Evaluation Comment",
                    max_chars=5000,
                )

                create_report = st.form_submit_button(
                    "Create Draft Report"
                )

            if create_report:
                result = api_request(
                    "POST",
                    f"{base_url}/reports",
                    json={
                        "final_comment": final_comment or None,
                    },
                )

                if result.status_code == 201:
                    st.success(
                        "Draft evaluation report created."
                    )
                    st.rerun()
                else:
                    display_api_error(result)

def main():
    st.title("🎓 Intelligent Academic Credentials Platform")

    if "token" not in st.session_state:
        st.session_state.token = None

    if not st.session_state.token:
        login_page()
        return

    try:
        response = api_request("GET", "/users/me")

        if response.status_code != 200:
            display_api_error(response)
            return

        user = response.json()
        role = get_role(user)

        st.sidebar.title("Account")
        st.sidebar.write(
            f"**User:** {user.get('email', 'Unknown')}"
        )
        st.sidebar.write(f"**Role:** {role}")

        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()

        if role == "CANDIDATE":
            candidate_dashboard()

        elif role == "SUPER_ADMIN":
            admin_dashboard()

        elif role == "REVIEWER":
            reviewer_dashboard()

        else:
            st.warning(
                f"No dashboard configured for role: {role}"
            )

    except requests.RequestException:
        st.error(
            "Cannot connect to FastAPI. "
            "Please check that the server is running."
        )

if __name__ == "__main__":
    main()