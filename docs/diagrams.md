# InvenTrack: Project Architecture & Mermaid Diagrams

## 1. System Architecture
```mermaid
flowchart LR
    subgraph Client["Frontend (React + Vite)"]
        UI["Admin Console & Home UI\n(Tailwind CSS, Recharts, Three.js)"]
        AuthClient["fetchWithAuth + JWT Storage\n(localStorage)"]
    end

    subgraph Backend["Backend (Django 4.2 + DRF)"]
        API["DRF ViewSets & Router\n(/api/categories, /api/products,\n/api/orders, /api/audit-logs)"]
        JWT["SimpleJWT Auth\n(/api/auth/login, /api/auth/token/refresh)"]
        Logic["Business Intelligence Layer\n(Stock Deduction & Audit Triggers)"]
    end

    subgraph Storage["Data & Media Layer"]
        DB[("SQLite / PostgreSQL\n(Category, Product, Order, InventoryLog, User)")]
        Media["Local Media Storage\n(/media/products/)"]
    end

    UI --> AuthClient
    AuthClient -- "HTTP / JSON + Bearer JWT" --> JWT
    AuthClient -- "REST API Calls" --> API
    JWT --> DB
    API --> Logic
    Logic --> DB
    API --> Media
```

## 2. Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    CATEGORY ||--o{ PRODUCT : "classifies"
    PRODUCT ||--o{ ORDER : "ordered_in"
    PRODUCT ||--o{ INVENTORY_LOG : "tracked_by"

    USER {
        int id PK
        string username
        string email
        string password
        boolean is_staff
    }

    CATEGORY {
        int id PK
        string name UK
    }

    PRODUCT {
        int id PK
        string name
        decimal price
        decimal costPrice
        int category_id FK
        int stock
        int minStockThreshold
        string batchNumber
        date expiryDate
        string location
        string image
        string unit
    }

    ORDER {
        int id PK
        string customerName
        int product_id FK
        int quantity
        date orderDate
        string status
    }

    INVENTORY_LOG {
        int id PK
        datetime timestamp
        int product_id FK
        string productName
        string type
        int quantityChange
        int newStock
        string reason
    }
```

## 3. Data Flow Diagram (DFD)
```mermaid
flowchart TD
    Admin(["Administrator"])

    subgraph Core["InvenTrack System"]
        P1["1.0 Authentication\n(JWT Login)"]
        P2["2.0 Category & Product\nManagement"]
        P3["3.0 Order Processing &\nStock Deduction"]
        P4["4.0 Audit Ledger &\nAnalytics Engine"]
    end

    D1[("Users Table")]
    D2[("Categories & Products")]
    D3[("Orders Table")]
    D4[("InventoryLog Ledger")]

    Admin -- "Email & Password" --> P1
    P1 -- "Verify" --> D1
    P1 -- "JWT Token" --> Admin

    Admin -- "CRUD Categories / Products" --> P2
    P2 -- "Store SKU & Stock" --> D2
    P2 -- "Initial / Manual Log" --> D4

    Admin -- "Create / Update Order" --> P3
    P3 -- "Save Order" --> D3
    P3 -- "Deduct Stock" --> D2
    P3 -- "Outbound Log" --> D4

    D2 --> P4
    D3 --> P4
    D4 --> P4
    P4 -- "KPIs, Charts, Audit Trail" --> Admin
```

## 4. Order & Stock Synchronization Sequence Diagram
```mermaid
sequenceDiagram
    actor Admin
    participant UI as Orders.jsx (React)
    participant API as OrderViewSet (DRF)
    participant DB as SQLite / PostgreSQL

    Admin->>UI: Fill New Order Form & Submit
    UI->>API: POST /api/orders (Bearer JWT, product ID, qty)
    API->>DB: Save Order record
    API->>DB: Deduct Product.stock -= quantity
    API->>DB: Create InventoryLog (type='Outbound', delta=-qty)
    DB-->>API: Saved Order + Updated Stock
    API-->>UI: 201 Created (Order JSON with product_name)
    UI-->>Admin: Update Orders Table & Dashboard State
```

## 5. Application Navigation & Use Case Flow
```mermaid
flowchart TD
    Start(["User Visits InvenTrack"]) --> Home["Public Landing Page (/)"]
    Home --> Login["Login Page (/login)"]
    Login --> Auth{"Valid JWT\nCredentials?"}
    Auth -- "No" --> Err["Show Error Message"] --> Login
    Auth -- "Yes" --> Admin["Protected Admin Console (/admin)"]

    Admin --> Dash["Dashboard Analytics\n(Revenue, Profit, Anomalies, Forecast)"]
    Admin --> Cat["Category Management\n(Create, Edit, Delete)"]
    Admin --> Prod["Product Catalog\n(SKU, Margin, Batch, Expiry, Image)"]
    Admin --> Ord["Order Management\n(Pending, Shipped, Delivered, Returned)"]
    Admin --> Logs["Movement Ledger\n(Inbound, Outbound, Adjustment Trail)"]
```
