# app.py
import sqlite3
from contextlib import closing
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")

# -----------------------------
# DB Helpers
# -----------------------------
@st.cache_resource
def get_conn(db_path: str = "food_management.db"):
    return sqlite3.connect(db_path, check_same_thread=False)

def run_query(query: str, params: tuple = ()):
    with closing(conn.cursor()) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
    return pd.DataFrame(rows, columns=cols)

def run_exec(query: str, params: tuple = ()):
    with closing(conn.cursor()) as cur:
        cur.execute(query, params)
        conn.commit()

# -----------------------------
# Cached lookups for filter UI
# -----------------------------
@st.cache_data
def get_distinct_values():
    cities = run_query("SELECT DISTINCT City FROM Providers UNION SELECT DISTINCT City FROM Receivers;")["City"].sort_values().tolist()
    providers = run_query("SELECT DISTINCT Name FROM Providers ORDER BY Name;")["Name"].tolist()
    food_types = run_query("SELECT DISTINCT Food_Type FROM Food_Listings ORDER BY Food_Type;")["Food_Type"].tolist()
    meal_types = run_query("SELECT DISTINCT Meal_Type FROM Food_Listings ORDER BY Meal_Type;")["Meal_Type"].tolist()
    provider_types = run_query("SELECT DISTINCT Provider_Type FROM Food_Listings ORDER BY Provider_Type;")["Provider_Type"].tolist()
    return cities, providers, food_types, meal_types, provider_types

# -----------------------------
# Charts (matplotlib only)
# -----------------------------
def barh(df, xcol, ycol, title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(df[ycol], df[xcol])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.invert_yaxis()
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    st.pyplot(fig)

def barv(df, xcol, ycol, title, xlabel, ylabel, rotate=45):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df[xcol], df[ycol])
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(df[xcol], rotation=rotate, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    st.pyplot(fig)

def lollipop_h(df, xcol, ycol, title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hlines(df[ycol], 0, df[xcol], colors='tab:blue', alpha=0.7)
    ax.plot(df[xcol], df[ycol], 'o', color='tab:blue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    st.pyplot(fig)

def lollipop_v(df, xcol, ycol, title, xlabel, ylabel, rotate=45):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.vlines(df[xcol], 0, df[ycol], colors='tab:green', alpha=0.7)
    ax.plot(df[xcol], df[ycol], 'o', color='tab:green')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xticklabels(df[xcol], rotation=rotate, ha='right')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    st.pyplot(fig)

def pie_chart(labels, sizes, title):
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.set_title(title)
    ax.axis('equal')
    st.pyplot(fig)

def line_chart(x, y, title, xlabel, ylabel):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, marker='o')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle='--', alpha=0.4)
    st.pyplot(fig)

# -----------------------------
# App UI
# -----------------------------
st.title("Local Food Wastage Management System")
st.caption("Filter listings, contact providers/receivers, perform CRUD, and explore insights.")

conn = get_conn()
cities, providers_list, food_types, meal_types, provider_types = get_distinct_values()

# ---- Sidebar Filters
st.sidebar.header("Filters")
sel_city = st.sidebar.selectbox("City (optional)", ["All"] + cities)
sel_provider = st.sidebar.selectbox("Provider (optional)", ["All"] + providers_list)
sel_food_type = st.sidebar.selectbox("Food Type (optional)", ["All"] + food_types)
sel_meal_type = st.sidebar.selectbox("Meal Type (optional)", ["All"] + meal_types)

# Build filter query
base_q = """
SELECT f.Food_ID, f.Food_Name, f.Quantity, f.Expiry_Date,
       f.Provider_ID, p.Name AS Provider_Name, f.Provider_Type,
       f.Location AS City, f.Food_Type, f.Meal_Type
FROM Food_Listings f
JOIN Providers p ON f.Provider_ID = p.Provider_ID
WHERE 1=1
"""
params = []
if sel_city != "All":
    base_q += " AND TRIM(LOWER(f.Location)) = TRIM(LOWER(?))"
    params.append(sel_city)
if sel_provider != "All":
    base_q += " AND TRIM(LOWER(p.Name)) = TRIM(LOWER(?))"
    params.append(sel_provider)
if sel_food_type != "All":
    base_q += " AND TRIM(LOWER(f.Food_Type)) = TRIM(LOWER(?))"
    params.append(sel_food_type)
if sel_meal_type != "All":
    base_q += " AND TRIM(LOWER(f.Meal_Type)) = TRIM(LOWER(?))"
    params.append(sel_meal_type)

listings_df = run_query(base_q + " ORDER BY f.Expiry_Date ASC;", tuple(params))

# ---- Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Listings & Map",
    "Contacts",
    "CRUD",
    "Analysis (15 Queries)"
])

# -----------------------------
# Tab 1: Listings
# -----------------------------
with tab1:
    st.subheader("Available Food Listings")
    st.dataframe(listings_df, use_container_width=True, hide_index=True)
    # simple KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Listings", f"{len(listings_df)}")
    c2.metric("Total Quantity", f"{int(listings_df['Quantity'].sum()) if not listings_df.empty else 0}")
    # Expiring soon
    if not listings_df.empty:
        soon = run_query("""
            SELECT Food_Name, Quantity, Expiry_Date, Provider_Name, City
            FROM (
                SELECT f.Food_Name, f.Quantity, f.Expiry_Date, p.Name AS Provider_Name, f.Location AS City
                FROM Food_Listings f
                JOIN Providers p ON f.Provider_ID = p.Provider_ID
            )
            WHERE julianday(Expiry_Date) - julianday(date('now')) <= 2
            ORDER BY Expiry_Date ASC
            LIMIT 10;
        """)
        c3.metric("Expiring ≤ 2 days", f"{len(soon)}")
    else:
        c3.metric("Expiring ≤ 2 days", "0")
    c4.metric("Cities (filter)", "All" if sel_city == "All" else sel_city)

# -----------------------------
# Tab 2: Contacts
# -----------------------------
with tab2:
    st.subheader("Contact Directory")
    city_for_contacts = st.selectbox("Choose a city for contacts", ["All"] + cities, key="contacts_city")
    prov_query = "SELECT Name, Type, Address, City, Contact FROM Providers"
    recv_query = "SELECT Name, Type, City, Contact FROM Receivers"
    if city_for_contacts != "All":
        prov_query += " WHERE TRIM(LOWER(City)) = TRIM(LOWER(?))"
        recv_query += " WHERE TRIM(LOWER(City)) = TRIM(LOWER(?))"
        prov_df = run_query(prov_query, (city_for_contacts,))
        recv_df = run_query(recv_query, (city_for_contacts,))
    else:
        prov_df = run_query(prov_query)
        recv_df = run_query(recv_query)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Providers**")
        st.dataframe(prov_df, use_container_width=True, hide_index=True)
    with c2:
        st.markdown("**Receivers**")
        st.dataframe(recv_df, use_container_width=True, hide_index=True)

# -----------------------------
# Tab 3: CRUD
# -----------------------------
with tab3:
    st.subheader("Create / Update / Delete")

    crud_tabs = st.tabs(["Add Provider", "Add Receiver", "Add Listing", "Add Claim", "Update Claim Status", "Delete Record"])

    # Add Provider
    with crud_tabs[0]:
        st.markdown("**Add a Provider**")
        ap_name = st.text_input("Name")
        ap_type = st.text_input("Type (Restaurant, Grocery Store, etc.)")
        ap_addr = st.text_input("Address")
        ap_city = st.text_input("City")
        ap_contact = st.text_input("Contact")
        if st.button("Add Provider"):
            if all([ap_name, ap_type, ap_addr, ap_city, ap_contact]):
                run_exec(
                    "INSERT INTO Providers (Name, Type, Address, City, Contact) VALUES (?, ?, ?, ?, ?);",
                    (ap_name, ap_type, ap_addr, ap_city, ap_contact)
                )
                st.success("Provider added.")
                get_distinct_values.clear()  # refresh caches
            else:
                st.error("Please fill all fields.")

    # Add Receiver
    with crud_tabs[1]:
        st.markdown("**Add a Receiver**")
        ar_name = st.text_input("Receiver Name")
        ar_type = st.text_input("Type (NGO, Community Center, Individual)")
        ar_city = st.text_input("City", key="recv_city")
        ar_contact = st.text_input("Contact", key="recv_contact")
        if st.button("Add Receiver"):
            if all([ar_name, ar_type, ar_city, ar_contact]):
                run_exec(
                    "INSERT INTO Receivers (Name, Type, City, Contact) VALUES (?, ?, ?, ?);",
                    (ar_name, ar_type, ar_city, ar_contact)
                )
                st.success("Receiver added.")
                get_distinct_values.clear()
            else:
                st.error("Please fill all fields.")

    # Add Listing
    with crud_tabs[2]:
        st.markdown("**Add a Food Listing**")
        # pick provider
        providers_df = run_query("SELECT Provider_ID, Name FROM Providers ORDER BY Name;")
        provider_pick = st.selectbox("Provider", providers_df["Name"].tolist())
        provider_id = int(providers_df.loc[providers_df["Name"] == provider_pick, "Provider_ID"].iloc[0])

        al_name = st.text_input("Food Name")
        al_qty = st.number_input("Quantity", min_value=1, step=1)
        al_exp = st.date_input("Expiry Date")
        al_ptype = st.selectbox("Provider Type", provider_types if provider_types else ["Restaurant", "Grocery Store"])
        al_loc = st.text_input("City (Location)")
        al_ftype = st.selectbox("Food Type", food_types if food_types else ["Vegetarian", "Non-Vegetarian", "Vegan"])
        al_mtype = st.selectbox("Meal Type", meal_types if meal_types else ["Breakfast", "Lunch", "Dinner", "Snacks"])

        if st.button("Add Listing"):
            if all([al_name, al_qty, al_exp, al_ptype, al_loc, al_ftype, al_mtype]):
                run_exec("""
                    INSERT INTO Food_Listings
                    (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (al_name, int(al_qty), al_exp.strftime("%Y-%m-%d"), provider_id, al_ptype, al_loc, al_ftype, al_mtype))
                st.success("Listing added.")
            else:
                st.error("Please fill all fields.")

    # Add Claim
    with crud_tabs[3]:
        st.markdown("**Add a Claim**")
        listings_pick = run_query("""
            SELECT Food_ID, Food_Name || ' | Qty:' || Quantity || ' | City:' || Location AS Label
            FROM Food_Listings ORDER BY Food_ID DESC LIMIT 200;
        """)
        recvs_df = run_query("SELECT Receiver_ID, Name FROM Receivers ORDER BY Name;")
        if listings_pick.empty or recvs_df.empty:
            st.info("Need at least one listing and one receiver.")
        else:
            claim_food_label = st.selectbox("Food Item", listings_pick["Label"].tolist())
            claim_food_id = int(listings_pick.loc[listings_pick["Label"] == claim_food_label, "Food_ID"].iloc[0])
            claim_recv_name = st.selectbox("Receiver", recvs_df["Name"].tolist())
            claim_recv_id = int(recvs_df.loc[recvs_df["Name"] == claim_recv_name, "Receiver_ID"].iloc[0])
            claim_status = st.selectbox("Status", ["Pending", "Completed", "Cancelled"])
            claim_time = st.date_input("Timestamp", value=datetime.now())
            if st.button("Create Claim"):
                run_exec("""
                    INSERT INTO Claims (Food_ID, Receiver_ID, Status, Timestamp)
                    VALUES (?, ?, ?, ?);
                """, (claim_food_id, claim_recv_id, claim_status, claim_time.strftime("%Y-%m-%d %H:%M:%S")))
                st.success("Claim created.")

    # Update Claim Status
    with crud_tabs[4]:
        st.markdown("**Update Claim Status**")
        claims_df = run_query("""
            SELECT c.Claim_ID, c.Status, c.Timestamp,
                   f.Food_Name, r.Name AS Receiver_Name
            FROM Claims c
            JOIN Food_Listings f ON c.Food_ID = f.Food_ID
            JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
            ORDER BY c.Claim_ID DESC LIMIT 300;
        """)
        if claims_df.empty:
            st.info("No claims to update.")
        else:
            st.dataframe(claims_df, use_container_width=True, hide_index=True)
            upd_id = st.number_input("Claim_ID to update", min_value=1, step=1)
            new_status = st.selectbox("New Status", ["Pending", "Completed", "Cancelled"], key="upd_status")
            if st.button("Update Status"):
                run_exec("UPDATE Claims SET Status = ? WHERE Claim_ID = ?;", (new_status, int(upd_id)))
                st.success("Status updated.")

    # Delete Record
    with crud_tabs[5]:
        st.markdown("**Delete a Record (be careful)**")
        del_table = st.selectbox("Table", ["Providers", "Receivers", "Food_Listings", "Claims"])
        del_id = st.number_input("Primary Key ID to delete", min_value=1, step=1)
        if st.button("Delete"):
            pk_map = {
                "Providers": "Provider_ID",
                "Receivers": "Receiver_ID",
                "Food_Listings": "Food_ID",
                "Claims": "Claim_ID"
            }
            run_exec(f"DELETE FROM {del_table} WHERE {pk_map[del_table]} = ?;", (int(del_id),))
            st.success(f"Deleted from {del_table}.")

# -----------------------------
# Tab 4: Analysis (15 Queries)
# -----------------------------
with tab4:
    st.subheader("SQL-Based Analysis and Visualizations")

    q_tabs = st.tabs([
        "1 Providers & Receivers by City",        # 1
        "2 Provider Type by Quantity",            # 2
        "3 Top Receivers by Claims",              # 3
        "4 Total Quantity (All)",                 # 4
        "5 Cities by Listings",                   # 5
        "6 Common Food Types",                    # 6
        "7 Claims per Food Item",                 # 7
        "8 Top Providers by Successful Claims",   # 8
        "9 Claim Status Share",                   # 9
        "10 Avg Qty per Receiver",                # 10
        "11 Meal Type Demand",                    # 11
        "12 Total Qty per Provider",              # 12
        "13 Peak Claim Hours",                    # 13
        "14 Cities by Total Quantity",            # 14
        "15 Timeliness vs Expiry"                 # 15
    ])

    # 1
    with q_tabs[0]:
        q = """
        SELECT City,
               COUNT(DISTINCT Provider_ID) AS Provider_Count,
               COUNT(DISTINCT Receiver_ID) AS Receiver_Count
        FROM (
            SELECT City, Provider_ID, NULL AS Receiver_ID FROM Providers
            UNION ALL
            SELECT City, NULL, Receiver_ID FROM Receivers
        )
        GROUP BY City;
        """
        df = run_query(q)
        df_top = df.sort_values(by=["Provider_Count","Receiver_Count"], ascending=False).head(10)
        st.dataframe(df_top, use_container_width=True, hide_index=True)
        barv(df_top.assign(Total=df_top["Provider_Count"]+df_top["Receiver_Count"]),
             "City", "Total", "Top 10 Cities by Providers+Receivers", "City", "Total")

    # 2
    with q_tabs[1]:
        q = """
        SELECT Provider_Type, SUM(Quantity) AS Total_Quantity
        FROM Food_Listings
        GROUP BY Provider_Type
        ORDER BY Total_Quantity DESC;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        barh(df, "Total_Quantity", "Provider_Type", "Total Food Quantity by Provider Type", "Quantity", "Provider Type")

    # 3
    with q_tabs[2]:
        q = """
        SELECT r.Name AS Receiver, COUNT(c.Claim_ID) AS Total_Claims
        FROM Claims c
        JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
        GROUP BY r.Name
        ORDER BY Total_Claims DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        lollipop_h(df, "Total_Claims", "Receiver", "Top Receivers by Number of Claims", "Claims", "Receiver")

    # 4
    with q_tabs[3]:
        q = "SELECT SUM(Quantity) AS Total_Quantity FROM Food_Listings;"
        df = run_query(q)
        st.metric("Total Food Quantity", int(df.iloc[0,0]) if not df.empty else 0)
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(["Total"], [df.iloc[0,0] if not df.empty else 0])
        ax.set_title("Total Quantity of Food Available")
        st.pyplot(fig)

    # 5
    with q_tabs[4]:
        q = """
        SELECT Location AS City, COUNT(*) AS Listing_Count
        FROM Food_Listings
        GROUP BY Location
        ORDER BY Listing_Count DESC;
        """
        df = run_query(q).head(10)
        st.dataframe(df, use_container_width=True, hide_index=True)
        barv(df, "City", "Listing_Count", "Top 10 Cities by Number of Listings", "City", "Listings")

    # 6
    with q_tabs[5]:
        q = """
        SELECT Food_Type, COUNT(*) AS Cnt
        FROM Food_Listings
        GROUP BY Food_Type
        ORDER BY Cnt DESC;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        pie_chart(df["Food_Type"].tolist(), df["Cnt"].tolist(), "Distribution of Food Types")

    # 7
    with q_tabs[6]:
        q = """
        SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claim_Count
        FROM Claims c
        JOIN Food_Listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Food_Name
        ORDER BY Claim_Count DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        lollipop_h(df, "Claim_Count", "Food_Name", "Top 10 Food Items by Claims", "Claims", "Food Item")

    # 8
    with q_tabs[7]:
        q = """
        SELECT p.Name AS Provider, COUNT(c.Claim_ID) AS Successful_Claims
        FROM Claims c
        JOIN Food_Listings f ON c.Food_ID = f.Food_ID
        JOIN Providers p ON f.Provider_ID = p.Provider_ID
        WHERE c.Status = 'Completed'
        GROUP BY p.Name
        ORDER BY Successful_Claims DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        lollipop_h(df, "Successful_Claims", "Provider", "Top Providers by Successful Claims", "Successful Claims", "Provider")

    # 9
    with q_tabs[8]:
        q = "SELECT Status, COUNT(*) AS Cnt FROM Claims GROUP BY Status;"
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        pie_chart(df["Status"].tolist(), df["Cnt"].tolist(), "Claim Status Breakdown")

    # 10
    with q_tabs[9]:
        q = """
        SELECT r.Name AS Receiver, AVG(f.Quantity) AS Avg_Qty
        FROM Claims c
        JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
        JOIN Food_Listings f ON c.Food_ID = f.Food_ID
        GROUP BY r.Name
        ORDER BY Avg_Qty DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        lollipop_v(df, "Receiver", "Avg_Qty", "Top Receivers by Avg Quantity Claimed", "Receiver", "Avg Quantity")

    # 11
    with q_tabs[10]:
        q = """
        SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Claim_Count
        FROM Claims c
        JOIN Food_Listings f ON c.Food_ID = f.Food_ID
        GROUP BY f.Meal_Type
        ORDER BY Claim_Count DESC;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        pie_chart(df["Meal_Type"].tolist(), df["Claim_Count"].tolist(), "Claims by Meal Type")

    # 12
    with q_tabs[11]:
        q = """
        SELECT p.Name AS Provider, SUM(f.Quantity) AS Total_Quantity
        FROM Food_Listings f
        JOIN Providers p ON f.Provider_ID = p.Provider_ID
        GROUP BY p.Name
        ORDER BY Total_Quantity DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        # Dot plot for names visibility
        fig, ax = plt.subplots(figsize=(8,5))
        ax.scatter(df["Total_Quantity"], df["Provider"], s=90)
        ax.set_title("Top Providers by Total Quantity Donated")
        ax.set_xlabel("Total Quantity")
        ax.set_ylabel("Provider")
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        st.pyplot(fig)

    # 13
    with q_tabs[12]:
        q = """
        SELECT strftime('%H', Timestamp) AS Hour, COUNT(Claim_ID) AS Claim_Count
        FROM Claims
        GROUP BY Hour
        ORDER BY Hour;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        line_chart(df["Hour"].tolist(), df["Claim_Count"].tolist(), "Food Claims by Hour", "Hour (24h)", "Claims")

    # 14
    with q_tabs[13]:
        q = """
        SELECT Location AS City, SUM(Quantity) AS Total_Quantity
        FROM Food_Listings
        GROUP BY Location
        ORDER BY Total_Quantity DESC
        LIMIT 10;
        """
        df = run_query(q)
        st.dataframe(df, use_container_width=True, hide_index=True)
        # Horizontal dot plot
        fig, ax = plt.subplots(figsize=(8,5))
        ax.scatter(df["Total_Quantity"], df["City"], s=100)
        ax.set_title("Top Cities by Total Quantity Donated")
        ax.set_xlabel("Total Quantity")
        ax.set_ylabel("City")
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        st.pyplot(fig)

    # 15
    with q_tabs[14]:
        q = """
        SELECT AVG(julianday(f.Expiry_Date) - julianday(c.Timestamp)) AS Avg_Days_Before_Expiry
        FROM Claims c
        JOIN Food_Listings f ON c.Food_ID = f.Food_ID
        WHERE c.Status = 'Completed';
        """
        df = run_query(q)
        avg_days = float(df.iloc[0,0]) if not df.empty and df.iloc[0,0] is not None else 0.0
        st.metric("Average days before expiry when food is claimed", f"{avg_days:.2f}")
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(["Avg Days Before Expiry"], [avg_days])
        ax.set_ylim(0, max(7, avg_days + 1))
        ax.set_title("Claim Timeliness vs Expiry")
        st.pyplot(fig)

st.caption("Built with Streamlit, SQLite, and Matplotlib.")
