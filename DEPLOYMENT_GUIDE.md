# Shala PWA - Deployment Guide

This guide will walk you through deploying the Shala PWA backend to Vercel and connecting it to a Supabase database.

## 1. Setup Supabase (Database)

1. Go to [Supabase](https://supabase.com/) and create a new project.
2. Once the project is created, navigate to **Project Settings -> Database**.
3. Scroll down to the **Connection string** section, click on the **URI** tab.
4. Copy the connection string. It will look something like this: `postgresql://postgres.[YOUR_PROJECT_REF]:[YOUR_PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`
5. Replace `[YOUR_PASSWORD]` with the password you created for the database.
6. Save this connection string; you will need it for Vercel.

## 2. Setup Vercel (Backend & Frontend Hosting)

1. Ensure your code is pushed to a GitHub, GitLab, or Bitbucket repository.
2. Go to [Vercel](https://vercel.com/) and log in.
3. Click **Add New -> Project**.
4. Import the repository containing the Shala PWA code.
5. In the **Configure Project** step:
   - **Framework Preset:** Leave it as "Other" (Vercel will detect Python via `vercel.json`).
   - **Root Directory:** `./` (or wherever `vercel.json` is located).
   - **Environment Variables:** You MUST add the following environment variables:
     - `SUPABASE_URL`: Paste the Supabase connection string you copied earlier. (Make sure it starts with `postgresql://`).
     - `JWT_SECRET`: Generate a random string (e.g., using `openssl rand -hex 32` in a terminal) or use a strong password. This secures user sessions.
     - `WHATSAPP_API_TOKEN`: Your token (`Nyy2fmv8qbEEpoidrLWGcBLZcYBAgPFqk08nBRodsL`).
     - `WHATSAPP_INSTANCE_ID`: Your instance ID (`instance4552`).
     - `FIREBASE_CREDENTIALS_JSON`: *(Optional but required for push notifications)* The raw JSON content of your Firebase Service Account key. You can get this from Firebase Console -> Project Settings -> Service Accounts -> Generate new private key. Open the downloaded file and paste the entire JSON object here.
6. Click **Deploy**.

## 3. Post-Deployment Steps

1. **Verify Database Creation:** When Vercel deploys, the FastAPI app starts up. In `main.py`, the line `Base.metadata.create_all(bind=engine)` automatically creates all necessary tables in your Supabase database on the first run.
2. **Seed Templates (Important):** You need to populate the database with the Arabic message templates.
   - Since the app is serverless, the easiest way is to temporarily run the seed script locally pointing to your production DB, or run it via a one-off task.
   - To do it locally:
     ```bash
     export SUPABASE_URL="your-production-supabase-url"
     python seed.py
     ```
     This will add the 7 required templates.
3. **View the App:** Once deployed, Vercel will provide a URL (e.g., `https://shala-pwa.vercel.app`). Navigate to this URL in your mobile browser or desktop browser.
   - You will see the main login screen.
   - Enter a phone number and click "Send OTP".
   - You should receive the OTP via WhatsApp. Enter it to log in.
   - To test without consuming WhatsApp API credits, you can check your Supabase `otp_codes` table to see the generated code.
4. **Access the Admin Dashboard:** Once logged in, click the "الإدارة (Admin)" tab at the bottom to view users and manage templates.
