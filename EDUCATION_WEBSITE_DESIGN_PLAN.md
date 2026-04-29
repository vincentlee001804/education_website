# Education Website Project - Design & Implementation Plan (Flask + MySQL)

## 1. Project goal
Build a responsive education website for undergraduate students that combines:
- Course learning resources (notes/videos/quizzes)
- A student portal (authentication, progress tracking, saved resources)
- A discussion forum / Q&A (peer interaction + moderation)
- A bookstore module (catalog + search + cart + checkout + purchase history)

The frontend will be plain **HTML/CSS/JavaScript** and will call a **Flask REST API** using `fetch()`. Data persistence will use **MySQL**.

## 2. Chosen stack
- Front-end: HTML, CSS, JavaScript (static pages)
- Back-end: Flask (REST API, JSON)
- Database: MySQL
- Auth: JSON Web Tokens (JWT) + secure password hashing (bcrypt/argon2)
- Data access: SQLAlchemy (recommended) or parameterized queries

## 3. Assumptions (confirm with your group)
1. Course resources are **notes + video only** (no quizzes for this project).
2. Video tutorials are provided as **YouTube links** (no custom video uploads required).
3. Notes are stored as **short text descriptions** (not file-based notes).
4. Bookstore supports **file upload for book images**.
5. Checkout is a **simulated purchase**. After purchase, users can **view/download the ebook as a protected PDF**.
6. Forum moderation actions are **role-based** (e.g., `moderator`, `admin`), with support for actions such as `hide`, `delete`, and `lock`.

## 4. Page map (frontend screens)
### 4.1 Homepage
- Navigation bar (Courses, Portal, Forum, Bookstore, Login/Register)
- Responsive hero section + quick links to popular courses/books

### 4.2 Course content pages
- Course listing (subject/module overview)
- Course detail page
  - Modules grouped by subject/module
  - Resources list per module (notes/videos/quizzes)
- Resource view page
  - Notes rendered as text/HTML snippet
  - Video embedded (if URL is provided)

### 4.3 Student portal
- Login/Register pages
- “My Progress”
  - completion status per resource
  - quiz scores (if quizzes are graded)
- “Saved Resources”
  - list resources bookmarked by the student

### 4.4 Discussion Forum / Q&A
- Topic list (search/filter optional)
- Topic page (thread of posts + reply UI)
- Post composer
- Reporting flow (report inappropriate content)
- Moderation UI (accessible only to moderators/admins)
  - list reported content
  - hide/delete/lock as allowed

### 4.5 Bookstore module
- Book catalog page
  - categories sidebar
  - search bar
  - results grid/list
- Book details page
  - title/author/description/category/price
  - “Add to cart” button
- Cart page
  - quantity update
  - total price
  - checkout button
- Checkout page
  - review order + finalize purchase
- Purchase history page (student portal section)
- After purchase: “My Ebooks” download/view page

## 5. REST API plan (Flask)
All API routes are JSON and should return consistent response shapes, e.g.:
`{ "data": ..., "error": null }` or `{ "error": { "code": "...", "message": "..." } }`.

### 5.1 Authentication
- `POST /api/auth/register`
  - creates a user + default role (student)
- `POST /api/auth/login`
  - verifies credentials, returns `{ access_token }`
- `GET /api/auth/me`
  - returns current user profile + role

### 5.2 Courses & learning resources
- `GET /api/courses` (optional subject filter)
- `GET /api/courses/<course_id>`
- `GET /api/courses/<course_id>/modules`
- `GET /api/modules/<module_id>/resources`
- `GET /api/resources/<resource_id>`

Student actions:
- `POST /api/resources/<resource_id>/complete`
- `POST /api/resources/<resource_id>/save`
- `DELETE /api/resources/<resource_id>/save`

### 5.3 Student progress
- `GET /api/progress`
  - aggregated progress summary for the logged-in user

### 5.4 Forum / Q&A
Topics:
- `GET /api/forum/topics`
- `POST /api/forum/topics`
- `GET /api/forum/topics/<topic_id>`

Posts:
- `POST /api/forum/topics/<topic_id>/posts`
- `POST /api/forum/posts/<post_id>/report`

Moderation (role protected):
- `GET /api/mod/reports`
- `POST /api/mod/reports/<report_id>/action`
  - action types example: `hide`, `delete`, `lock_topic`, `approve`
- Direct moderation endpoints (optional but recommended for UI simplicity):
  - `POST /api/mod/topics/<topic_id>/lock`
  - `POST /api/mod/topics/<topic_id>/hide`
  - `POST /api/mod/posts/<post_id>/hide`
  - `DELETE /api/mod/posts/<post_id>` (soft-delete or permanent delete per your DB choice)

### 5.5 Bookstore
- `GET /api/books` (supports `search`, `category`, `min_price`, `max_price`)
- `GET /api/books/<book_id>`
- `GET /api/books/categories`

Cart:
- `GET /api/cart`
- `POST /api/cart/items`
  - body: `{ "book_id": ..., "quantity": ... }`
- `PATCH /api/cart/items/<item_id>`
- `DELETE /api/cart/items/<item_id>`

Checkout / orders:
- `POST /api/checkout`
  - validates inventory availability
  - creates order + order_items
  - decrements inventory (stock_count)
  - marks order as `paid` (simulated)
- `GET /api/orders` (purchase history)
- `GET /api/orders/<order_id>` (optional)

Ebook access (protected):
- `GET /api/ebooks` (list books the user purchased)
- `GET /api/ebooks/<book_id>/download`
  - checks JWT + verifies user owns the book via `orders` + `order_items`
  - returns/streams the PDF as `application/pdf` with `Content-Disposition: attachment`

## 6. MySQL data model (schema outline)
This is a practical starter schema; you can refine during implementation.

### 6.1 Users & roles
- `users`
  - `id` (PK)
  - `email` (unique)
  - `password_hash`
  - `display_name`
  - `created_at`
  - `is_active`
- `roles`
  - `id` (PK)
  - `name` (`student`, `admin`, `moderator`)
- `user_roles`
  - `user_id` (FK)
  - `role_id` (FK)

### 6.2 Courses & resources
- `subjects` (optional)
  - `id`, `name`
- `courses`
  - `id`, `title`, `subject_id` (nullable), `description`
- `modules`
  - `id`, `course_id`, `title`, `order_index`
- `resources`
  - `id`, `module_id`, `title`, `resource_type` (`note`, `video`, `quiz`), `content_text` (nullable), `content_url` (nullable)
- `quizzes` (optional separate table if quizzes need structure)
  - `id`, `resource_id`, `questions_json` or normalized question tables

### 6.3 Student progress & saved resources
- `resource_completions`
  - `user_id`, `resource_id`, `completed_at`
- `quiz_attempts`
  - `user_id`, `quiz_id`, `score`, `submitted_at`
- `saved_resources`
  - `user_id`, `resource_id`, `saved_at`

### 6.4 Forum
- `forum_topics`
  - `id`, `title`, `created_by`, `created_at`, `is_locked`, `status` (`active`, `hidden`)
- `forum_posts`
  - `id`, `topic_id`, `content`, `created_by`, `created_at`, `status` (`visible`, `hidden`)
- `forum_reports`
  - `id`, `post_id`, `reporter_id`, `reason`, `created_at`, `status` (`open`, `resolved`)

### 6.5 Bookstore
- `book_categories`
  - `id`, `name`
- `books`
  - `id`, `title`, `author`, `description`, `category_id`, `price`, `image_url` (nullable)
- `inventory`
  - `book_id` (PK/FK), `stock_count`, `updated_at`

Ebook PDFs:
- `ebooks`
  - `book_id` (PK/FK)
  - `pdf_url` (or `pdf_path`), `original_filename`, `file_size_bytes`
  - `created_at`, `updated_at`

Cart & orders:
- `carts`
  - `id`, `user_id`, `status` (`active`, `checked_out`)
- `cart_items`
  - `id`, `cart_id`, `book_id`, `quantity`, `unit_price_snapshot`
- `orders`
  - `id`, `user_id`, `total_amount`, `status` (`paid`, `cancelled`), `created_at`
- `order_items`
  - `id`, `order_id`, `book_id`, `quantity`, `unit_price_snapshot`

### 6.6 Purchase history queries
Purchase history comes from `orders` + `order_items`.

## 7. Security plan (what must be protected)
1. **Password security**
   - Hash passwords with `bcrypt` or `argon2`
2. **Authorization**
   - Every moderation endpoint must verify role (`admin/moderator`) server-side
3. **Input validation**
   - Validate and sanitize forum content, topic titles, checkout requests, and search parameters
4. **SQL safety**
   - Use SQLAlchemy ORM or parameterized queries to prevent SQL injection
5. **JWT safety**
   - Short-lived access token (e.g., 15 mins)
   - Store tokens in memory or secure storage strategy (avoid leaking via XSS)
6. **Rate limiting**
   - Rate limit login/register and forum posting/reporting
7. **File upload security (images + PDF)**
   - Allowlist MIME types (image/* for book images, application/pdf for ebooks)
   - Enforce file size limits
   - Store uploaded files outside the public web root (or behind protected routes)
   - Randomize filenames and avoid trusting user-provided names
   - Re-validate file type server-side (do not rely on client)

## 8. Accessibility (A11y) plan
1. Semantic HTML: headings, landmarks (`nav`, `main`, `section`)
2. Keyboard navigation: ensure all interactive elements are reachable via `Tab`
3. Visible focus states for buttons/links
4. Contrast: ensure text vs background is readable
5. Images: provide `alt` text for book images and decorative icons
6. ARIA: use only when necessary (e.g., for modal dialogs)

## 9. Usability plan
1. Consistent navigation on every page
2. Clear empty states (e.g., “No saved resources yet”)
3. Search feedback (loading, “no results found”)
4. Cart and checkout with clear totals and error messages (e.g., “insufficient stock”)

## 10. Implementation process (milestones)
### Milestone 1: Project foundation
- Flask app + configuration
- MySQL connection + initial schema migration/scripts
- Authentication (register/login/me)

### Milestone 2: Bookstore module (end-to-end)
- Books catalog + categories endpoint
- Cart endpoints
- Checkout endpoint (inventory validation)
- Purchase history page
- Upload support (admin/mod):
  - book image upload
  - ebook PDF upload
- Protected ebook download endpoint

### Milestone 3: Courses + student portal
- Course listing + course/resource pages
- Progress tracking endpoints
- Saved resources endpoints

### Milestone 4: Forum / Q&A + moderation
- Topic and post creation flow
- Report content flow
- Moderator/admin endpoints + moderation UI
- Moderator actions implemented (`hide`, `delete`, `lock`) and role-guarded server-side

### Milestone 5: Final integration + documentation
- Responsive UI polish
- Security hardening pass (authz checks, validation, rate limiting)
- Accessibility audit pass
- Complete the required documentation sections

## 11. What documentation you will submit
When your implementation is done, update this file or create a final report that includes:
1. Design choices and rationale (based on this plan)
2. Implementation process (milestones + key challenges)
3. Reflection on usability, accessibility, and security (what improved, what trade-offs you made)

## 12. Reasonable default rubric (self-check)
Use this as a proxy for how a typical web technology project is assessed. Adjust percentages if your lecturer uses different criteria.

### 12.1 Functionality coverage (30%)
- Homepage exists and is responsive
- Course pages show notes + YouTube videos (organized by module)
- Student portal supports register/login and personalized features (progress + saved resources)
- Forum/Q&A supports posting, reporting, and moderator actions (`hide`, `delete`, `lock`)
- Bookstore supports categories + search, cart, simulated checkout, purchase history
- After checkout, users can access ebooks via protected PDF download

### 12.2 UI/UX creativity & quality (25%)
- Visually engaging and consistent design across pages
- Good information architecture (navigation is intuitive)
- Clear, user-friendly empty states and error handling
- Responsive mobile experience (no broken layouts)

### 12.3 Usability & accessibility (20%)
- Semantic HTML, keyboard navigability, visible focus styles
- Color contrast is adequate
- Images have meaningful `alt` text
- Modals/forms are accessible (labels, ARIA only when needed)

### 12.4 Security (15%)
- Server-side authorization for moderation endpoints and ebook downloads
- Password hashing is used
- Input validation on forum posts and checkout/cart endpoints
- File upload validation (type/size) and safe storage strategy
- JWT is short-lived; endpoints require authentication

### 12.5 Documentation & implementation process (10%)
- Clear explanation of design choices and rationale
- Implementation milestones described with key decisions/trade-offs
- Security/usability/accessibility reflection includes what was tested/improved

