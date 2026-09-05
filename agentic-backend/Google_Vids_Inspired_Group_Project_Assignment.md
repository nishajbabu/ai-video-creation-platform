# Group Project Assignment
## Google Vids-Inspired AI Video Creation Platform

### Objective
Build a functional AI-powered video creation prototype inspired by the workflow and key capabilities of Google Vids. The project should use appropriate Agentic AI, LLM, media-generation, backend and frontend technologies.

This is not a direct copy of Google Vids. Study the workflow, identify useful capabilities and build your own implementation. The completed project may also be used as a demo/showcase for prospective client discussions.

---

# Team Module Ownership

| Candidate | Module | Primary Responsibility |
|---|---|---|
| Ilavarasan V | Agentic AI + Backend | Planner, Script & Storyboard Agents and backend APIs |
| Shamsu Nisha N | Video Editor | Scene editor, timeline, preview and editing |
| Nishaj Ahmed Babu | Documents + Assets | File processing, RAG and asset management |
| Agathiyan R K | AI Media Generation | Voice, avatar and AI video generation |
| Athim R | Frontend + Integration | Dashboard, project workflow and frontend integration |

Each person owns their assigned module, but **the entire team is responsible for integration and the final working product**.

---

# Expected End-to-End Workflow

```text
User
  |
  v
Create Video Request
  |
  v
AI Planner Agent
  |
  +----> Script Generation
  |
  +----> Storyboard / Scene Planning
  |
  v
Scene Plan
  |
  +----> Documents / Knowledge / Assets
  |
  +----> AI Images / Video
  |
  +----> Voice / Audio
  |
  v
Video Editor / Timeline
  |
  v
Preview
  |
  v
Final Video
```

Example:

> Create a 60-second product introduction video for our AI chatbot.

The system should generate a storyboard, create or select appropriate media, generate narration, allow editing and produce a final video.

---

# 1. Ilavarasan V - Agentic AI + Backend

## Objective

Build the intelligence and orchestration layer of the application.

## Responsibilities

Implement:

- LLM integration
- Planner Agent
- Script Generation Agent
- Storyboard / Scene Planning Agent
- Agent workflow/orchestration
- Agent state management
- Backend APIs
- Project/video data models
- Error handling and logging

## Expected Workflow

```text
User Requirement
      |
      v
Planner Agent
      |
      v
Script Agent
      |
      v
Storyboard Agent
      |
      v
Structured Scene Plan
```

## Expected Deliverables

- Working agents
- Backend APIs
- Agent workflow
- API documentation
- Unit tests
- Integration support for other modules

---

# 2. Shamsu Nisha N - Video Editor + Timeline

## Objective

Build the editing experience that converts generated scenes and media into an editable video.

## Responsibilities

Implement:

- Scene list
- Timeline
- Scene ordering
- Add/remove scene
- Scene duration
- Text overlays
- Media placement
- Transitions
- Preview
- Basic editing
- Video export

## Expected Deliverables

- Functional video editor
- Timeline implementation
- Preview
- Scene management
- Export functionality
- Tests
- Documentation

---

# 3. Nishaj Ahmed Babu - Documents, RAG + Asset Management

## Objective

Allow users to provide supporting documents and media that can be used during AI video generation.

## Responsibilities

Implement:

- File upload
- PDF/DOCX processing
- Text extraction
- Document chunking
- Embeddings
- Retrieval
- Relevant information extraction
- Asset library
- Image/video upload
- Asset-to-scene mapping

## Expected Workflow

```text
Product.pdf
    |
    v
Document Processing
    |
    v
Extract Information
    |
    v
RAG / Retrieval
    |
    v
Relevant Product Information
    |
    v
Storyboard / Scene Generation
```

## Expected Deliverables

- Document processing service
- RAG/retrieval pipeline
- Asset management
- APIs
- Tests
- Documentation

---

# 4. Agathiyan R K - AI Media Generation

## Objective

Implement AI-generated audio and visual media required for the video.

## Responsibilities

### Voice

- Text-to-Speech
- Voice selection
- Scene-wise narration
- Audio generation
- Audio preview

### AI Visuals

Where practical, integrate an available API/model for:

- AI image generation
- AI video generation
- Scene-based visual generation

### Optional

- Avatar generation
- Talking avatar
- Lip-sync

## Expected Workflow

```text
Scene Script
    |
    +------> Text-to-Speech
    |             |
    |             v
    |          Voiceover
    |
    +------> Visual Prompt
                  |
                  v
            AI Media Generation
                  |
                  v
             Scene Assets
```

The candidate is not expected to build an AI video-generation model from scratch. The focus is on **clean integration, API abstraction, error handling, and connecting generated media to the overall workflow**.

## Expected Deliverables

- TTS integration
- AI media integration
- Media storage
- APIs
- Tests
- Documentation

---

# 5. Athim R - Frontend + Project Workflow

## Objective

Build the main application interface and connect all backend modules into a usable product.

## Responsibilities

### Dashboard

- Projects
- Create project
- Open project
- Rename project
- Delete project
- Project status

### Create Video

Provide:

- User prompt
- File upload
- Video duration
- Video style
- Generate button

Example:

```text
What do you want to create?

[ Create a product introduction video
  for our AI platform                         ]

Supporting files:
[ + Upload Files ]

Duration:
( ) 30 seconds
( ) 60 seconds
( ) 90 seconds

[ Generate Storyboard ]
```

### Integration

Connect:

- Agent APIs
- Document APIs
- Media APIs
- Editor APIs
- Project APIs

The user should be able to complete the end-to-end workflow without manually calling APIs.

## Expected Deliverables

- Dashboard
- Create Video workflow
- Project management
- API integration
- Responsive UI
- Tests
- Documentation

---

# Planning Requirements

## Important

**Do not start implementation immediately.**

Before development, the team must prepare and submit **one consolidated technical plan**.

The plan should clearly demonstrate that the team understands the product, architecture, responsibilities, dependencies and implementation approach.

---

## A. Product Understanding

Document:

- Problem statement
- Target users
- Core use cases
- User journey
- Key workflows
- Features inspired by the reference product

Categorize features into:

- Must Have
- Should Have
- Nice to Have

---

## B. System Architecture

Provide:

- High-Level Architecture
- Component Diagram
- Sequence Diagram
- Data Flow Diagram
- Deployment Diagram

Clearly show how the five modules communicate.

---

## C. Agentic AI Architecture

Define:

- Agents
- Agent responsibilities
- Inputs
- Outputs
- Agent communication
- State management
- Failure handling
- Human intervention, if applicable

---

## D. API Contracts

Before implementation, define the APIs between modules.

For each API document:

- Endpoint
- HTTP method
- Request
- Response
- Authentication
- Validation
- Error response

---

## E. Database / Storage Design

Define the required data structures for:

- User
- Project
- Video
- Scene
- Asset
- Audio
- Generated media
- Metadata

Include an ER diagram where applicable.

---

## F. Task Breakdown

Prepare a detailed task list.

| Task | Owner | Dependency | Expected Output | Priority |
|---|---|---|---|---|
| Planner Agent | Ilavarasan | None | Working planner | High |
| Scene Editor | Shamsu | Scene API | Editable scenes | High |
| PDF Processing | Nishaj | None | Extracted content | High |
| TTS Integration | Agathiyan | Script API | Audio file | High |
| Dashboard | Athim | API contracts | Working UI | High |

The assigned module ownership provides the initial responsibility split. The team should further break each module into **specific implementation tasks, dependencies, and milestones**.

---

# Integration Requirements

All team members must follow:

- Common Git repository
- Feature branches
- Pull requests
- Meaningful commit messages
- Common API contracts
- Environment configuration
- `.env.example`
- Consistent error responses
- README updates
- Unit tests
- Integration tests

No module should be developed in complete isolation.

The team must regularly integrate modules and verify the complete workflow.

---

# Expected Final Product

The final application should demonstrate an end-to-end workflow where:

1. User creates a video project.
2. User enters a video requirement.
3. User optionally uploads a supporting document.
4. AI generates a script/storyboard.
5. Relevant information/assets are retrieved.
6. AI-generated media/audio is created.
7. Scenes are loaded into the editor.
8. User can modify the scenes.
9. User previews the video.
10. User exports the final video.

---

# Required Deliverables

The team must produce:

## Planning

- Problem Statement
- Product/Feature Analysis
- User Workflow
- System Architecture
- Agentic AI Architecture
- Technology Stack
- API Contracts
- Database/Storage Design
- Module Breakdown
- Task Allocation
- Dependency Mapping
- Risk Analysis

## Implementation

- Source Code
- Git Repository
- Working Application
- Backend APIs
- Frontend
- Agentic AI Components
- Media Generation Components
- Tests
- Docker Configuration
- Environment Configuration

## Documentation

- README
- Architecture Documentation
- API Documentation
- Setup Instructions
- Module Documentation
- Known Limitations

## Final Demonstration

The team should be able to demonstrate the complete user journey from:

**User Requirement → AI Planning → Script/Storyboard → Assets/Media → Editing → Preview → Final Video**

The team should also be prepared to explain individual contributions and technical decisions.

---

# Assessment Focus

| Area | Focus |
|---|---|
| Technical Understanding | Understanding of assigned module |
| Architecture | Quality of system and module design |
| Agentic AI | Appropriate use of agents and orchestration |
| Implementation | Working features |
| Integration | Ability to work with other modules |
| Code Quality | Maintainability and structure |
| Problem Solving | Handling technical challenges |
| Testing | Unit and integration testing |
| Documentation | Technical clarity |
| Team Collaboration | Communication and ownership |
| Final Demo | End-to-end working product |

---

# Important Expectations

The objective is not to implement the maximum number of features.

Priority should be:

**Understand → Plan → Design → Build → Integrate → Test → Demonstrate**

A smaller number of well-designed, well-integrated, working features is preferred over a large number of incomplete features.

Each team member should have clear ownership of their module while also contributing to the overall integration and final product.
