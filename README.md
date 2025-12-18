# 👶 Baby Development Timeline

A digital family photo album where parents can document their baby's growth with photos and measurements, and share specific moments with family members.

## 🎯 Project Overview

**Core motivation:** Gift for family to track baby's development. Built with Python and Streamlit for rapid development.

**Tech Stack (Free Tier):**
- **Frontend/Backend:** Streamlit (deployed on Streamlit Community Cloud)
- **Database + Auth + Storage:** Supabase (500MB database, 1GB storage)
- **Language:** Python

## ✨ Features (MVP)

- ✅ Admin authentication (1-2 users)
- ✅ Photo upload with captions
- ✅ Height/weight measurements tracking
- ✅ Combined timeline view
- ✅ Growth charts (Plotly)
- ✅ Family sharing via private links (password-optional)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Supabase account (free tier)
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd lil_heart
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Supabase:**
   - Create account at [https://supabase.com](https://supabase.com)
   - Create new project: "baby-timeline-prod"
   - Run SQL migrations from `supabase_migrations/`
   - Create storage bucket: `baby-photos` (private)

5. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

6. **Run the app:**
   ```bash
   streamlit run Timeline.py
   ```

## 📁 Project Structure

```
lil_heart/
├── Timeline.py                      # Main entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── .streamlit/config.toml      # Streamlit theme
├── src/
│   ├── auth.py                 # Authentication logic
│   ├── database.py             # Database operations
│   ├── storage.py              # Photo storage
│   ├── sharing.py              # Family sharing
│   └── utils.py                # Helper functions
├── pages/
│   ├── 1_📸_Upload_Photo.py
│   ├── 2_📏_Add_Measurement.py
│   ├── 3_📊_Growth_Chart.py
│   └── 4_🔗_Sharing.py
└── supabase_migrations/
    ├── 01_create_tables.sql
    └── 02_enable_rls.sql
```

## 🔐 Security

- **Authentication:** Supabase Auth with email/password
- **Authorization:** Row Level Security (RLS) at database level
- **Sharing:** UUID v4 tokens (128-bit random) with optional password protection
- **Storage:** Image optimization (max 1920px, 85% JPEG quality)

## 📚 Documentation

See the full plan and specification in: `.claude/plans/fuzzy-plotting-diffie.md`

## 🛠️ Development Phases

- [x] Phase 0: Project setup
- [ ] Phase 1: Supabase database schema
- [ ] Phase 2: Admin authentication
- [ ] Phase 3: Photo upload & storage
- [ ] Phase 4: Measurements CRUD
- [ ] Phase 5: Growth chart visualization
- [ ] Phase 6: Family sharing
- [ ] Phase 7: Polish & testing
- [ ] Phase 8: Deployment

## 📝 License

Private project - Not for public distribution

## 🤝 Contributing

This is a personal project for family use. Not accepting external contributions.

## 📧 Contact

Questions? Check the plan file or ask the development team.
