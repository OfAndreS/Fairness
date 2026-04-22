
You are a strict data engineering system. Classify the exact database variables provided into ONE of the permitted categories. You MUST strictly follow these exact definitions:

PERMITTED CATEGORIES AND STRICT RULES:
- SOCIOECONOMIC: Home ownership, number of children/dependents, household size, length of employment, employment status, occupation, family income, income, wealth, parents’ income, social class, education.
- DEMOGRAPHIC: Age, gender, ethnicity, marital status, family life cycle. (CRITICAL: DO NOT put geographical locations here).
- VALUES, ATTITUDES and BEHAVIORAL: Socio-motivation, attitudes toward debt, perceived financial wellbeing, religious practices, consumer behavior, spending pattern, attitudes toward money, risk-taking, compulsive buying, delay of gratification, financial knowledge.
- INSTITUTIONAL and FINANCIAL: Number of debts, length of relationship with the bank, number of bank accounts, debt to income ratio, total financial assets, payment pattern, credit limit, existing credit commitments, credit score, number of credit cards, past credit history, loan amount, taking debt advice, loan duration, account balance, purpose of loan.
- PERSONALITY: Self-control, emotional stability, intelligence, optimism, extraversion, impulsiveness.
- SITUATIONAL: STRICTLY Adverse life events or life-altering events. (CRITICAL: DO NOT put standard dates, terms, or housing here).
- EDUCATIONAL: Field of study, GPA (Grade Point Average), year at school. (General education level goes to SOCIOECONOMIC).
- MACROECONOMIC: General economic indicators (inflation, GDP).
- HEALTH-RELATED: Physical and mental health indicators.
- ALTERNATIVE: Social network patterns, posting time, friends, daily calls, SMS patterns, disclosure of social media profile, and geographical locations (city, zipcode, region, country, IP).
- UNCLASSIFIED: System IDs, gibberish, transaction IDs, passwords, hashes, pure system metadata.

OUTPUT RULES:
1. Return ONLY a JSON object.
2. The keys MUST be the exact variable names provided.
3. The values MUST be the exact permitted category strings.
4. One key-value pair per variable.

RAW VARIABLES TO CLASSIFY:
- ID: CRED-74 | Variable: ActiveLateLastPaymentCategory
- ID: CRED-75 | Variable: step
- ID: CRED-75 | Variable: type
- ID: CRED-75 | Variable: amount
- ID: CRED-75 | Variable: nameOrig
- ID: CRED-75 | Variable: oldbalanceOrg
- ID: CRED-75 | Variable: newbalanceOrig
- ID: CRED-75 | Variable: nameDest
- ID: CRED-75 | Variable: oldbalanceDest
- ID: CRED-75 | Variable: newbalanceDest
- ID: CRED-75 | Variable: isFraud
- ID: CRED-75 | Variable: isFlaggedFraud
- ID: CRED-76 | Variable: ID
- ID: CRED-76 | Variable: Customer_ID
- ID: CRED-76 | Variable: Month
- ID: CRED-76 | Variable: Name
- ID: CRED-76 | Variable: Age
- ID: CRED-76 | Variable: SSN
- ID: CRED-76 | Variable: Occupation
- ID: CRED-76 | Variable: Annual_Income
- ID: CRED-76 | Variable: Monthly_Inhand_Salary
- ID: CRED-76 | Variable: Num_Bank_Accounts
- ID: CRED-76 | Variable: Num_Credit_Card
- ID: CRED-76 | Variable: Interest_Rate
- ID: CRED-76 | Variable: Num_of_Loan
- ID: CRED-76 | Variable: Type_of_Loan
- ID: CRED-76 | Variable: Delay_from_due_date
- ID: CRED-76 | Variable: Num_of_Delayed_Payment
- ID: CRED-76 | Variable: Changed_Credit_Limit
- ID: CRED-76 | Variable: Num_Credit_Inquiries
- ID: CRED-76 | Variable: Credit_Mix
- ID: CRED-76 | Variable: Outstanding_Debt
- ID: CRED-76 | Variable: Credit_Utilization_Ratio
- ID: CRED-76 | Variable: Credit_History_Age
- ID: CRED-76 | Variable: Payment_of_Min_Amount
- ID: CRED-76 | Variable: Total_EMI_per_month
- ID: CRED-76 | Variable: Amount_invested_monthly
- ID: CRED-76 | Variable: Payment_Behaviour
- ID: CRED-76 | Variable: Monthly_Balance
- ID: CRED-77 | Variable: ip_region_mismatch
- ID: CRED-77 | Variable: device_change_rate
- ID: CRED-77 | Variable: application_frequency
- ID: CRED-77 | Variable: loan_amount
- ID: CRED-77 | Variable: institution
- ID: CRED-77 | Variable: loan_type
- ID: CRED-77 | Variable: session_duration
- ID: CRED-77 | Variable: geo_location_consistency
- ID: CRED-77 | Variable: previous_defaults
- ID: CRED-77 | Variable: time_between_apps
- ID: CRED-77 | Variable: browser_fingerprint_change
- ID: CRED-77 | Variable: fraudulent
- ID: CRED-78 | Variable: Cust_Num
- ID: CRED-78 | Variable: Payment_Method_description
- ID: CRED-78 | Variable: Document_No
- ID: CRED-78 | Variable: Amount
- ID: CRED-78 | Variable: Amount_Bins
- ID: CRED-78 | Variable: Clearing_doc
- ID: CRED-78 | Variable: Zipcode
- ID: CRED-78 | Variable: Region
- ID: CRED-78 | Variable: City
- ID: CRED-78 | Variable: Customer_Name
- ID: CRED-78 | Variable: Age_Of_Customer_Months
- ID: CRED-78 | Variable: Age_Of_Customer_Year
- ID: CRED-78 | Variable: Customer_Age_Year_Bins
- ID: CRED-78 | Variable: Payment_Term
- ID: CRED-78 | Variable: Payment_Term_Bins
- ID: CRED-78 | Variable: Days_Overdue_Delay
- ID: CRED-78 | Variable: Delay_Bins
- ID: CRED-78 | Variable: Doc_Date
- ID: CRED-78 | Variable: Net_Due_Date
- ID: CRED-78 | Variable: Posting_Date
- ID: CRED-78 | Variable: Clearing_date
- ID: CRED-78 | Variable: No_of_orders_by_customer
- ID: CRED-78 | Variable: Rank_of_order_by_customer
- ID: CRED-78 | Variable: Weekday_clearing
- ID: CRED-78 | Variable: Weekday_due
- ID: CRED-78 | Variable: Quarter_clearing
- ID: CRED-78 | Variable: DelayFlag
- ID: CRED-78 | Variable: Weekday_clearnum
- ID: CRED-78 | Variable: Weekday_due.1
- ID: CRED-79 | Variable: Transaction_ID
- ID: CRED-79 | Variable: Customer_ID
- ID: CRED-79 | Variable: Transaction_Date
- ID: CRED-79 | Variable: Transaction_Time
- ID: CRED-79 | Variable: Customer_Age
- ID: CRED-79 | Variable: Customer_Loyalty_Tier
- ID: CRED-79 | Variable: Location
- ID: CRED-79 | Variable: Store_ID
- ID: CRED-79 | Variable: Product_SKU
- ID: CRED-79 | Variable: Product_Category
- ID: CRED-79 | Variable: Purchase_Amount
- ID: CRED-79 | Variable: Payment_Method
- ID: CRED-79 | Variable: Device_Type
- ID: CRED-79 | Variable: IP_Address
- ID: CRED-79 | Variable: Fraud_Flag
- ID: CRED-79 | Variable: Footfall_Count
