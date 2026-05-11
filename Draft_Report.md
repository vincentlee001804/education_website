# Introduction
This report details the design, implementation, and evaluation of a responsive, full-stack education website built to support undergraduate students in their academic journey. The platform integrates a centralized learning hub with specialized modules, including course content delivery, a personalized student portal, an interactive discussion forum, and a functional e-commerce bookstore. The project aims to deliver a secure, accessible, and highly usable environment that successfully blends academic resource management with digital purchasing capabilities.

1.0 Design Choices and Rationale
1.1 Architecture Choice
The project uses a Flask-based full-stack architecture with server-rendered pages and JSON APIs under `/api`.
This hybrid approach was chosen to balance development speed and flexibility:
Server-rendered templates simplify page structure and routing for core views.
JSON APIs allow modular frontend interactions (for cart actions, forum posting, and progress updates) using JavaScript `fetch()`.
Keeping both in one codebase reduces setup overhead and makes integration easier for our project.

1.2 Technology Stack
The selected stack is:
Backend: Flask + Flask-SQLAlchemy
Authentication: Flask-JWT-Extended
Database: SQLite (an equivalent relational database used for local development, utilizing SQLAlchemy ORM to allow seamless transition to MySQL for production)
Frontend: HTML, CSS, JavaScript

This stack was selected because it is lightweight, beginner-friendly, and well-supported. It enables rapid iteration while still supporting important real-world concepts like API design, role-based authorization, and data persistence.

1.3 Module-Based Product Design
The system is divided into clear modules:
Homepage (central, responsive navigation hub connecting all other modules)
Course learning module (courses, modules, resources such as lecture notes and video tutorials, completion tracking)
Student portal (authentication, saved resources, progress)
Forum/Q&A module (topics, posts, reporting, moderation)
Bookstore module (catalog, cart, checkout, purchase history, ebook access)
This modular design improves maintainability and allows team members to work in parallel with minimal conflicts. It also maps directly to user needs, so each module provides a focused feature set.

1.4 Security-by-Default Decisions
Several security-focused design choices were included early:
Passwords are stored as hashes, not plaintext.
JWT is required for protected endpoints (cart, checkout, progress, posting).
Moderation APIs are role-protected (admin/moderator).
Ebook download is ownership-checked to prevent unauthorized access.
Input handling is validated server-side to reduce abuse and malformed requests.

These decisions were prioritized because the platform includes user accounts, downloadable content, and user-generated forum content.


2.0 Implementation Process
2.1 Planning and Requirement Breakdown
Implementation started with a page map and API plan. Core user flows were defined first:
Register/login and access personalized features.
Browse learning resources and track completion.
Participate in forum discussions safely.
Discover books, checkout, and access purchased ebooks.
Defining these flows upfront helped keep backend routes, database entities, and frontend pages aligned.

2.2 Incremental Development Approach
The project was implemented in milestones:
Milestone 1: Foundation
Flask app setup and project structure
Database models and seed-ready schema baseline
Authentication endpoints and login/register pages

Milestone 2: Bookstore End-to-End
Catalog and categories
Cart operations and checkout logic
Order history and protected ebook access

Milestone 3: Courses and Student Portal
Course and module browsing
Resource completion tracking
Saved-resource features

Milestone 4: Forum and Moderation
Topic/post creation and thread interaction
Reporting workflow
Moderator/admin actions for unsafe content

Milestone 5: Integration and Quality Pass
UI consistency and responsive behavior improvements
Security and validation review
Documentation completion

2.3 Challenges and Resolutions
Key implementation challenges included:
State consistency between server-rendered pages and API-driven interactions.
Resolved by standardizing API responses and using predictable frontend update flows.
Access control complexity for different user actions.
Resolved through endpoint-level JWT checks and role verification.
Feature integration across modules (e.g., linking checkout outcomes to ebook availability).
Resolved by keeping relationships explicit in models and reusing shared user identity context.

2.4 Testing and Validation
Validation focused on practical workflow testing:
Authentication and session/JWT-protected endpoint checks
Bookstore transaction flow from cart to order history
Progress/saved-resource accuracy
Forum posting and moderation behavior
Error paths (invalid inputs, unauthorized attempts, missing resources)


3.0 Reflection on Usability, Accessibility, and Security
3.1 Usability Reflection
The product emphasizes straightforward navigation and clear user tasks:
Responsive layout for desktop and mobile, ensuring the website is accessible and functional across all device sizes.
Consistent menu structure across major pages reduces learning time.
Core actions (add to cart, save resource, create post) are visible and direct.
User-facing feedback for empty states and failed actions supports recovery.

A key trade-off was breadth vs depth: delivering multiple modules in one semester required prioritizing complete core flows over highly advanced interface polish.

3.2 Accessibility Reflection
Accessibility considerations were included during UI implementation:
Semantic page structure and meaningful headings
Labeling of form controls and clear action buttons
Keyboard-friendly interaction patterns for common controls
Attention to readable contrast and text clarity

Further improvement opportunities include a more formal accessibility audit (e.g., WCAG checklist and screen-reader-specific testing across all pages).

3.3 Security Reflection
Security was treated as a required engineering concern, not an add-on:
Authentication and authorization guard sensitive operations.
Input validation reduces misuse risk on forum and transactional endpoints.
Ownership checks protect paid digital assets.
Secrets are externalized via environment variables for safer deployment practices.

Remaining improvements for production readiness could include stronger rate limiting, expanded audit logging, stricter file handling policies, and comprehensive automated security tests.

3.4 Overall Lessons Learned
For this project, our team learned that good web engineering is not only about the quantity of the features, but also the satisfaction of user experience, the accessibility for all types of users and the secure handling of the data and permissions that were trusted to be given to us. Early planning with the team, modular boundaries and interactive validation were the most effective practices we found in keeping the project stable while delivering multiple connected features.
