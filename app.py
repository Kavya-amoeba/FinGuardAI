import streamlit as st
import sqlite3
import pandas as pd
import hashlib
from datetime import date, datetime
from io import BytesIO

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="FinGuardAI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_NAME = "expenses.db"

# =========================================================
# DATABASE
# =========================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            expense_date TEXT NOT NULL,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


init_database()

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password):
    conn = get_connection()

    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def login_user(username, password):
    conn = get_connection()

    result = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hash_password(password))
    ).fetchone()

    conn.close()
    return result is not None


def add_expense(name, category, amount, expense_date, description):
    conn = get_connection()

    conn.execute("""
        INSERT INTO expenses
        (expense_name, category, amount, expense_date, description)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        category,
        amount,
        expense_date,
        description
    ))

    conn.commit()
    conn.close()


def get_expenses():
    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC",
        conn
    )

    conn.close()
    return df


def delete_expense(expense_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM expenses WHERE id = ?",
        (expense_id,)
    )
    conn.commit()
    conn.close()


def clear_expenses():
    conn = get_connection()
    conn.execute("DELETE FROM expenses")
    conn.commit()
    conn.close()


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "login_mode" not in st.session_state:
    st.session_state.login_mode = "login"


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 0;
}

.subtitle {
    font-size: 18px;
    opacity: 0.75;
    margin-top: 4px;
}

.section-title {
    font-size: 28px;
    font-weight: 750;
    margin-top: 15px;
    margin-bottom: 8px;
}

.metric-card {
    padding: 20px;
    border-radius: 15px;
    border: 1px solid rgba(128,128,128,0.20);
    background: rgba(128,128,128,0.06);
    min-height: 130px;
}

.metric-title {
    font-size: 15px;
    opacity: 0.7;
}

.metric-value {
    font-size: 30px;
    font-weight: 800;
    margin-top: 8px;
}

.insight-box {
    padding: 18px;
    border-radius: 14px;
    border: 1px solid rgba(128,128,128,0.20);
    background: rgba(128,128,128,0.05);
    margin-bottom: 12px;
}

.home-title {
    text-align: center;
    font-size: 52px;
    font-weight: 850;
    margin-top: 50px;
}

.home-subtitle {
    text-align: center;
    font-size: 20px;
    opacity: 0.75;
    margin-bottom: 30px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.markdown(
        '<div class="home-title">💰 FinGuardAI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="home-subtitle">YOUR MONEY. YOUR FUTURE.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; font-size:18px;">
        An intelligent personal finance assistant that helps you
        track expenses, understand spending and make smarter financial decisions.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")
    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📊 Track Expenses")
        st.write(
            "Record daily expenses and keep your financial activity organized."
        )

    with col2:
        st.subheader("🎯 Manage Budget")
        st.write(
            "Set your monthly budget and monitor how much you have spent."
        )

    with col3:
        st.subheader("🤖 Smart Insights")
        st.write(
            "Get personalized recommendations based on your spending pattern."
        )

    st.write("")
    st.write("")

    col_left, col_center, col_right = st.columns([1, 2, 1])

    with col_center:
        if st.button(
            "🚀 GET STARTED",
            width="stretch"
        ):
            st.session_state.page = "dashboard"
            st.rerun()

        if st.button(
            "🔐 Login / Sign Up",
            width="stretch"
        ):
            st.session_state.page = "auth"
            st.rerun()


# =========================================================
# AUTHENTICATION PAGE
# =========================================================

def auth_page():

    st.title("🔐 FinGuardAI Account")

    if st.session_state.login_mode == "login":

        st.subheader("Welcome Back")

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "🔑 Login",
            width="stretch"
        ):

            if not username or not password:
                st.warning("Please enter both username and password.")

            elif login_user(username, password):

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "dashboard"

                st.success("Login successful!")
                st.rerun()

            else:
                st.error("Invalid username or password.")

        st.write("")

        if st.button("Create a new account"):
            st.session_state.login_mode = "signup"
            st.rerun()

    else:

        st.subheader("Create Account")

        username = st.text_input("Choose Username")
        password = st.text_input(
            "Choose Password",
            type="password"
        )
        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "📝 Create Account",
            width="stretch"
        ):

            if not username or not password:
                st.warning("Please fill in all fields.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            elif len(password) < 4:
                st.warning("Password should contain at least 4 characters.")

            elif register_user(username, password):
                st.success(
                    "Account created successfully. You can now log in."
                )
                st.session_state.login_mode = "login"

            else:
                st.error("Username already exists.")

        st.write("")

        if st.button("Already have an account? Login"):
            st.session_state.login_mode = "login"
            st.rerun()

    st.write("")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

def dashboard_sidebar():

    with st.sidebar:

        st.title("💰 FinGuardAI")

        st.caption("Personal Finance Assistant")

        st.divider()

        if st.session_state.logged_in:
            st.success(
                f"Logged in as {st.session_state.username}"
            )

        if st.button(
            "🏠 Home",
            width="stretch"
        ):
            st.session_state.page = "home"
            st.rerun()

        if st.button(
            "📊 Dashboard",
            width="stretch"
        ):
            st.session_state.page = "dashboard"
            st.rerun()

        if st.button(
            "➕ Add Expense",
            width="stretch"
        ):
            st.session_state.page = "add_expense"
            st.rerun()

        if st.button(
            "📈 Analytics",
            width="stretch"
        ):
            st.session_state.page = "analytics"
            st.rerun()

        if st.button(
            "🤖 AI Insights",
            width="stretch"
        ):
            st.session_state.page = "insights"
            st.rerun()

        if st.button(
            "📄 Reports",
            width="stretch"
        ):
            st.session_state.page = "reports"
            st.rerun()

        st.divider()

        if st.button(
            "🗑️ Manage Expenses",
            width="stretch"
        ):
            st.session_state.page = "manage"
            st.rerun()

        st.divider()

        if st.session_state.logged_in:

            if st.button(
                "🚪 Logout",
                width="stretch"
            ):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.session_state.page = "home"
                st.rerun()


# =========================================================
# FINANCIAL DATA
# =========================================================

def get_financial_data():

    df = get_expenses()

    income = 30000.0
    budget = 20000.0

    if df.empty:
        total_expenses = 0
    else:
        total_expenses = df["amount"].sum()

    savings = income - total_expenses

    budget_remaining = budget - total_expenses

    savings_rate = (
        (savings / income) * 100
        if income > 0
        else 0
    )

    budget_used = (
        (total_expenses / budget) * 100
        if budget > 0
        else 0
    )

    return (
        df,
        income,
        budget,
        total_expenses,
        savings,
        budget_remaining,
        savings_rate,
        budget_used
    )


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    dashboard_sidebar()

    (
        df,
        income,
        budget,
        total_expenses,
        savings,
        budget_remaining,
        savings_rate,
        budget_used
    ) = get_financial_data()

    st.markdown(
        '<div class="main-title">📊 Financial Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Your complete financial overview</div>',
        unsafe_allow_html=True
    )

    st.write("")

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    cols = st.columns(4)

    with cols[0]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Monthly Income</div>
                <div class="metric-value">₹{income:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with cols[1]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total Expenses</div>
                <div class="metric-value">₹{total_expenses:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with cols[2]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Available Savings</div>
                <div class="metric-value">₹{savings:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with cols[3]:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Budget Remaining</div>
                <div class="metric-value">₹{budget_remaining:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.write("")

    # -----------------------------------------------------
    # FINANCIAL HEALTH
    # -----------------------------------------------------

    health_score = max(
        0,
        min(
            100,
            round(
                100 - (budget_used * 0.5) + (savings_rate * 0.25)
            )
        )
    )

    st.subheader("❤️ Financial Health")

    health_col1, health_col2 = st.columns([1, 2])

    with health_col1:

        st.metric(
            "Health Score",
            f"{health_score}/100"
        )

        if health_score >= 80:
            st.success("Excellent financial health")
        elif health_score >= 60:
            st.info("Good financial health")
        elif health_score >= 40:
            st.warning("Needs attention")
        else:
            st.error("High spending risk")

    with health_col2:

        st.write("Budget Usage")

        st.progress(
            min(max(budget_used / 100, 0), 1)
        )

        st.caption(
            f"{budget_used:.1f}% of your monthly budget used"
        )

        st.write("Savings Rate")

        st.progress(
            min(max(savings_rate / 100, 0), 1)
        )

        st.caption(
            f"{savings_rate:.1f}% of your income is currently saved"
        )

    st.divider()

    # -----------------------------------------------------
    # QUICK ADD EXPENSE
    # -----------------------------------------------------

    st.subheader("➕ Quick Add Expense")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        name = st.text_input(
            "Expense Name",
            placeholder="Example: Lunch"
        )

    with col2:
        category = st.selectbox(
            "Category",
            [
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Bills",
                "Entertainment",
                "Health",
                "Other"
            ]
        )

    with col3:
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=50.0
        )

    with col4:
        expense_date = st.date_input(
            "Date",
            value=date.today()
        )

    description = st.text_input(
        "Description (optional)"
    )

    if st.button(
        "💾 Add Expense",
        width="stretch"
    ):

        if not name.strip():
            st.warning("Please enter an expense name.")

        elif amount <= 0:
            st.warning("Please enter an amount greater than ₹0.")

        else:

            add_expense(
                name.strip(),
                category,
                amount,
                expense_date.isoformat(),
                description.strip()
            )

            st.success("Expense added successfully!")
            st.rerun()

    st.divider()

    # -----------------------------------------------------
    # RECENT EXPENSES
    # -----------------------------------------------------

    st.subheader("🧾 Recent Expenses")

    if df.empty:

        st.info(
            "No expenses recorded yet. Add your first expense above."
        )

    else:

        display_df = df.head(5).copy()

        display_df["amount"] = display_df["amount"].apply(
            lambda x: f"₹{x:,.2f}"
        )

        display_df = display_df[
            [
                "expense_name",
                "category",
                "amount",
                "expense_date",
                "description"
            ]
        ]

        display_df.columns = [
            "Expense",
            "Category",
            "Amount",
            "Date",
            "Description"
        ]

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )

    st.divider()

    # -----------------------------------------------------
    # MINI ANALYTICS
    # -----------------------------------------------------

    st.subheader("📈 Spending Snapshot")

    if not df.empty:

        category_data = (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.bar_chart(category_data)

        with chart_col2:

            daily_data = (
                df.groupby("expense_date")["amount"]
                .sum()
            )

            st.line_chart(daily_data)

    else:

        st.info("Add expenses to see your spending analytics.")

    st.divider()

    st.subheader("🤖 Smart Summary")

    if total_expenses == 0:

        st.info(
            "Start adding expenses and FinGuardAI will analyze your spending."
        )

    else:

        if budget_used < 50:
            st.success(
                "🟢 You are comfortably within your monthly budget."
            )
        elif budget_used < 80:
            st.info(
                "🟡 Your spending is moderate. Keep monitoring your budget."
            )
        else:
            st.warning(
                "🔴 Your spending is approaching or exceeding your budget."
            )

        if savings_rate >= 30:
            st.success(
                f"💰 Great job! Your current savings rate is {savings_rate:.1f}%."
            )
        else:
            st.warning(
                f"💡 Your current savings rate is {savings_rate:.1f}%. "
                "Consider reducing non-essential spending."
            )


# =========================================================
# ADD EXPENSE PAGE
# =========================================================

def add_expense_page():

    dashboard_sidebar()

    st.title("➕ Add New Expense")
    st.write(
        "Record a new transaction and keep your financial history organized."
    )

    st.divider()

    with st.form("expense_form"):

        col1, col2 = st.columns(2)

        with col1:

            name = st.text_input(
                "Expense Name *",
                placeholder="Example: College Bus"
            )

            category = st.selectbox(
                "Category *",
                [
                    "Food",
                    "Travel",
                    "Shopping",
                    "Education",
                    "Bills",
                    "Entertainment",
                    "Health",
                    "Other"
                ]
            )

        with col2:

            amount = st.number_input(
                "Amount (₹) *",
                min_value=0.0,
                step=50.0
            )

            expense_date = st.date_input(
                "Expense Date",
                value=date.today()
            )

        description = st.text_area(
            "Description",
            placeholder="Add a short note about this expense..."
        )

        submitted = st.form_submit_button(
            "💾 Save Expense",
            width="stretch"
        )

        if submitted:

            if not name.strip():
                st.error("Expense name is required.")

            elif amount <= 0:
                st.error("Amount must be greater than ₹0.")

            else:

                add_expense(
                    name.strip(),
                    category,
                    amount,
                    expense_date.isoformat(),
                    description.strip()
                )

                st.success(
                    f"₹{amount:,.2f} expense added successfully!"
                )

    st.divider()

    st.subheader("💡 Expense Entry Tips")

    tips = st.columns(3)

    with tips[0]:
        st.write("📝 **Use clear names**")
        st.caption("Example: Lunch, Bus Pass, Books")

    with tips[1]:
        st.write("🏷️ **Choose the right category**")
        st.caption("This improves your analytics.")

    with tips[2]:
        st.write("📅 **Keep dates accurate**")
        st.caption("This makes spending trends more useful.")


# =========================================================
# ANALYTICS PAGE
# =========================================================

def analytics_page():

    dashboard_sidebar()

    st.title("📈 Spending Analytics")
    st.write(
        "Understand where your money is going."
    )

    df = get_expenses()

    if df.empty:

        st.info(
            "No expense data available yet. Add some expenses first."
        )
        return

    total = df["amount"].sum()

    average = df["amount"].mean()

    highest = df["amount"].max()

    number = len(df)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Spent", f"₹{total:,.0f}")
    col2.metric("Average Expense", f"₹{average:,.0f}")
    col3.metric("Largest Expense", f"₹{highest:,.0f}")
    col4.metric("Transactions", number)

    st.divider()

    # Category analysis

    st.subheader("🏷️ Spending by Category")

    category_data = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    st.bar_chart(category_data)

    st.divider()

    # Daily trend

    st.subheader("📅 Spending Trend")

    daily_data = (
        df.groupby("expense_date")["amount"]
        .sum()
    )

    st.line_chart(daily_data)

    st.divider()

    # Category percentage

    st.subheader("📊 Category Distribution")

    percentage_data = (
        category_data / total * 100
    ).round(1)

    percentage_df = percentage_data.reset_index()

    percentage_df.columns = [
        "Category",
        "Percentage"
    ]

    st.dataframe(
        percentage_df,
        width="stretch",
        hide_index=True
    )

    st.divider()

    # Biggest spending

    st.subheader("🔎 Top Expenses")

    top_expenses = df.sort_values(
        "amount",
        ascending=False
    ).head(5)

    top_display = top_expenses[
        [
            "expense_name",
            "category",
            "amount",
            "expense_date"
        ]
    ].copy()

    top_display["amount"] = top_display["amount"].apply(
        lambda x: f"₹{x:,.2f}"
    )

    top_display.columns = [
        "Expense",
        "Category",
        "Amount",
        "Date"
    ]

    st.dataframe(
        top_display,
        width="stretch",
        hide_index=True
    )


# =========================================================
# AI INSIGHTS
# =========================================================

def insights_page():

    dashboard_sidebar()

    st.title("🤖 AI Financial Insights")

    st.write(
        "FinGuardAI analyzes your spending data and generates personalized recommendations."
    )

    (
        df,
        income,
        budget,
        total_expenses,
        savings,
        budget_remaining,
        savings_rate,
        budget_used
    ) = get_financial_data()

    if df.empty:

        st.info(
            "Add expenses first. Your AI insights will appear here."
        )
        return

    category_data = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    highest_category = category_data.index[0]

    highest_category_amount = category_data.iloc[0]

    highest_category_percentage = (
        highest_category_amount / total_expenses * 100
    )

    st.subheader("🧠 Personalized Analysis")

    # Budget insight

    if budget_used >= 100:

        st.error(
            f"🔴 **Budget Alert:** You have exceeded your monthly budget by "
            f"₹{abs(budget_remaining):,.0f}."
        )

    elif budget_used >= 80:

        st.warning(
            f"🟠 **Budget Warning:** You have already used "
            f"{budget_used:.1f}% of your monthly budget."
        )

    elif budget_used >= 50:

        st.info(
            f"🟡 **Budget Status:** You have used "
            f"{budget_used:.1f}% of your monthly budget."
        )

    else:

        st.success(
            f"🟢 **Budget Status:** Your spending is comfortably below "
            f"your monthly budget."
        )

    # Savings insight

    if savings_rate >= 30:

        st.success(
            f"💰 **Strong Savings:** Your current savings rate is "
            f"{savings_rate:.1f}%. Keep maintaining this habit."
        )

    elif savings_rate >= 20:

        st.info(
            f"💡 **Healthy Savings:** Your savings rate is "
            f"{savings_rate:.1f}%. Try gradually improving it."
        )

    else:

        st.warning(
            f"⚠️ **Savings Opportunity:** Your savings rate is only "
            f"{savings_rate:.1f}%. Look for areas where spending can be reduced."
        )

    # Category insight

    st.info(
        f"🏷️ **Top Spending Category:** {highest_category} accounts for "
        f"{highest_category_percentage:.1f}% of your total spending "
        f"(₹{highest_category_amount:,.0f})."
    )

    # Large expense insight

    largest_expense = df.loc[
        df["amount"].idxmax()
    ]

    st.warning(
        f"🔎 **Largest Transaction:** "
        f"{largest_expense['expense_name']} — "
        f"₹{largest_expense['amount']:,.0f}."
    )

    # Number of transactions

    if len(df) >= 10:

        st.info(
            "📊 You have recorded many transactions. "
            "Review your weekly spending regularly."
        )

    else:

        st.info(
            "📊 Continue recording expenses to help FinGuardAI "
            "identify stronger spending patterns."
        )

    st.divider()

    st.subheader("🎯 Smart Recommendations")

    recommendations = []

    if budget_used >= 80:
        recommendations.append(
            "Reduce non-essential purchases until your budget usage falls."
        )

    if highest_category_percentage >= 40:
        recommendations.append(
            f"Review your {highest_category.lower()} spending because it represents "
            f"more than 40% of your current expenses."
        )

    if savings_rate < 20:
        recommendations.append(
            "Try setting aside part of your income before making discretionary purchases."
        )

    if savings_rate >= 30:
        recommendations.append(
            "Your savings performance is strong. Continue maintaining this discipline."
        )

    if not recommendations:
        recommendations.append(
            "Your spending pattern currently looks balanced. Keep tracking consistently."
        )

    for recommendation in recommendations:

        st.markdown(
            f"""
            <div class="insight-box">
            💡 {recommendation}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.caption(
        "Note: These are rule-based AI-style recommendations generated from your entered financial data."
    )


# =========================================================
# REPORTS PAGE
# =========================================================

def reports_page():

    dashboard_sidebar()

    st.title("📄 Financial Reports")

    st.write(
        "Generate a professional summary of your financial activity."
    )

    (
        df,
        income,
        budget,
        total_expenses,
        savings,
        budget_remaining,
        savings_rate,
        budget_used
    ) = get_financial_data()

    st.divider()

    # Summary

    st.subheader("📋 Financial Summary")

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric(
            "Monthly Income",
            f"₹{income:,.0f}"
        )

    with summary_col2:
        st.metric(
            "Total Expenses",
            f"₹{total_expenses:,.0f}"
        )

    with summary_col3:
        st.metric(
            "Savings",
            f"₹{savings:,.0f}"
        )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Monthly Budget",
            f"₹{budget:,.0f}"
        )

    with col2:
        st.metric(
            "Budget Used",
            f"{budget_used:.1f}%"
        )

    with col3:
        st.metric(
            "Savings Rate",
            f"{savings_rate:.1f}%"
        )

    st.divider()

    # Category report

    st.subheader("🏷️ Category Report")

    if not df.empty:

        category_report = (
            df.groupby("category")["amount"]
            .sum()
            .reset_index()
        )

        category_report.columns = [
            "Category",
            "Total Spent"
        ]

        category_report["Percentage"] = (
            category_report["Total Spent"]
            / total_expenses
            * 100
        ).round(1)

        category_report["Total Spent"] = (
            category_report["Total Spent"]
            .round(2)
        )

        st.dataframe(
            category_report,
            width="stretch",
            hide_index=True
        )

    else:

        st.info("No expenses available for the report.")

    st.divider()

    # Expense report

    st.subheader("🧾 Detailed Expense Report")

    if not df.empty:

        report_df = df.copy()

        report_df = report_df[
            [
                "id",
                "expense_name",
                "category",
                "amount",
                "expense_date",
                "description"
            ]
        ]

        report_df.columns = [
            "ID",
            "Expense",
            "Category",
            "Amount",
            "Date",
            "Description"
        ]

        st.dataframe(
            report_df,
            width="stretch",
            hide_index=True
        )

        csv_data = report_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="⬇️ Download Expense Report (CSV)",
            data=csv_data,
            file_name="FinGuardAI_Expense_Report.csv",
            mime="text/csv",
            width="stretch"
        )

    else:

        st.info(
            "Add expenses to generate your detailed report."
        )

    st.divider()

    st.subheader("📌 Report Summary")

    if total_expenses == 0:

        st.write(
            "No spending has been recorded yet."
        )

    else:

        st.write(
            f"During the current tracking period, total recorded expenses "
            f"are ₹{total_expenses:,.2f}. "
            f"Your available savings are approximately ₹{savings:,.2f}, "
            f"with a savings rate of {savings_rate:.1f}%."
        )


# =========================================================
# MANAGE EXPENSES
# =========================================================

def manage_page():

    dashboard_sidebar()

    st.title("🗑️ Manage Expenses")

    df = get_expenses()

    if df.empty:

        st.info("There are no expenses to manage.")
        return

    st.subheader("All Expenses")

    display_df = df.copy()

    display_df["amount"] = display_df["amount"].apply(
        lambda x: f"₹{x:,.2f}"
    )

    display_df.columns = [
        "ID",
        "Expense",
        "Category",
        "Amount",
        "Date",
        "Description"
    ]

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )

    st.divider()

    st.subheader("Delete an Expense")

    expense_options = {
        f"{row['expense_name']} — ₹{row['amount']:,.2f} — {row['expense_date']}":
        row["id"]
        for _, row in df.iterrows()
    }

    selected = st.selectbox(
        "Select expense",
        list(expense_options.keys())
    )

    if st.button(
        "🗑️ Delete Selected Expense",
        width="stretch"
    ):

        delete_expense(
            expense_options[selected]
        )

        st.success("Expense deleted successfully.")
        st.rerun()

    st.divider()

    st.subheader("⚠️ Advanced Data Management")

    st.warning(
        "The following action permanently removes all expense records."
    )

    if st.button(
        "Delete ALL Expenses",
        width="stretch"
    ):

        clear_expenses()

        st.success(
            "All expenses have been deleted."
        )

        st.rerun()


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.page == "home":

    # Hide sidebar on home page
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    home_page()


elif st.session_state.page == "auth":

    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    auth_page()


elif st.session_state.page == "dashboard":

    dashboard_page()


elif st.session_state.page == "add_expense":

    add_expense_page()


elif st.session_state.page == "analytics":

    analytics_page()


elif st.session_state.page == "insights":

    insights_page()


elif st.session_state.page == "reports":

    reports_page()


elif st.session_state.page == "manage":

    manage_page()


# =========================================================
# FOOTER
# =========================================================

st.write("")

st.markdown(
    """
    <div style="text-align:center; opacity:0.55; padding:20px;">
    💰 FinGuardAI • Smart Personal Finance Assistant<br>
    Built with Python, Streamlit & SQLite
    </div>
    """,
    unsafe_allow_html=True
)