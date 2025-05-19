-- PostgreSQL version of the Vineyard Inventory database

-- Create the database
-- Note: In PostgreSQL, this is typically done with CREATE DATABASE command, 
-- but when using Docker, the database is created by environment variables

-- Drop tables if they exist
DROP TABLE IF EXISTS vine_issues;
DROP TABLE IF EXISTS inventory_checks;
DROP TABLE IF EXISTS maintenance_activities;
DROP TABLE IF EXISTS maintenance_types;
DROP TABLE IF EXISTS vine_inventory;
DROP TABLE IF EXISTS users;

-- Create the table to store user information
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,        -- Unique identifier for each user
    user_name VARCHAR(255) NOT NULL,   -- Name of the user
    user_role VARCHAR(100) NOT NULL    -- Role of the user (e.g., manager, worker)
);

-- Create the table to store vine inventory
CREATE TABLE vine_inventory (
    vine_id SERIAL PRIMARY KEY,                        -- Unique identifier for each vine
    alpha_numeric_id VARCHAR(50) NOT NULL UNIQUE,      -- Alphanumeric identifier for each vine
    year_of_planting INTEGER NOT NULL,                 -- Year the vine was planted
    nursery VARCHAR(255) NOT NULL,                     -- Name of the nursery
    variety VARCHAR(255) NOT NULL,                     -- Variety of the grapevine
    rootstock VARCHAR(255) NOT NULL,                   -- Type of rootstock used
    vineyard_name VARCHAR(255) NOT NULL,               -- Name of the vineyard
    field_name VARCHAR(255) NOT NULL,                  -- Name of the field where planted
    row_number INTEGER NOT NULL,                       -- Row number within the field
    spot_number INTEGER NOT NULL,                      -- Spot number within the row
    is_dead BOOLEAN NOT NULL DEFAULT FALSE,            -- Indicates if the vine is dead
    date_died TIMESTAMP DEFAULT NULL,                  -- Date and time the vine died
    record_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP -- Date and time the record was created
);

-- Add an index for quick searching by field, row, and spot
CREATE INDEX idx_field_row_spot 
ON vine_inventory (field_name, row_number, spot_number);

-- Create the table to list all maintenance types
CREATE TABLE maintenance_types (
    type_id SERIAL PRIMARY KEY,               -- Unique identifier for each maintenance type
    type_name VARCHAR(255) NOT NULL UNIQUE,   -- Name of the maintenance type (e.g., pruning, fertilizing)
    description TEXT DEFAULT NULL             -- Optional description of the maintenance type
);

-- Create the table to store maintenance activities
CREATE TABLE maintenance_activities (
    activity_id SERIAL PRIMARY KEY,           -- Unique identifier for each activity
    vine_id INTEGER NOT NULL,                 -- The vine associated with the activity
    type_id INTEGER NOT NULL,                 -- The type of maintenance activity
    activity_date TIMESTAMP NOT NULL,         -- Date and time of the activity
    notes TEXT DEFAULT NULL,                  -- Additional notes about the activity
    FOREIGN KEY (vine_id) REFERENCES vine_inventory(vine_id), -- Foreign key to link to vine_inventory
    FOREIGN KEY (type_id) REFERENCES maintenance_types(type_id) -- Foreign key to link to maintenance_types
);

-- Create the table to store periodic inventory checks
CREATE TABLE inventory_checks (
    check_id SERIAL PRIMARY KEY,              -- Unique identifier for each inventory check
    check_date TIMESTAMP NOT NULL,            -- Date and time the inventory check was performed
    vine_id INTEGER NOT NULL,                 -- The vine being checked
    checked_by VARCHAR(255) NOT NULL,         -- Name of the person who performed the check
    FOREIGN KEY (vine_id) REFERENCES vine_inventory(vine_id) -- Foreign key to link to vine_inventory
);

-- Create the table to store vine issues
CREATE TABLE vine_issues (
    issue_id SERIAL PRIMARY KEY,              -- Unique identifier for each issue
    vine_id INTEGER NOT NULL,                 -- The vine associated with the issue
    issue_description TEXT NOT NULL,          -- Description of the issue (e.g., broken water emitter)
    photo_path VARCHAR(255) DEFAULT NULL,     -- Path to a photo of the issue
    date_reported TIMESTAMP NOT NULL,         -- Date and time the issue was reported
    reported_by INTEGER NOT NULL,             -- ID of the person who reported the issue
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE, -- Whether the issue has been resolved
    date_resolved TIMESTAMP DEFAULT NULL,     -- Date and time the issue was resolved
    resolved_by INTEGER DEFAULT NULL,         -- ID of the person who resolved the issue
    FOREIGN KEY (vine_id) REFERENCES vine_inventory(vine_id), -- Foreign key to link to vine_inventory
    FOREIGN KEY (reported_by) REFERENCES users(user_id), -- Foreign key to link to users
    FOREIGN KEY (resolved_by) REFERENCES users(user_id) -- Foreign key to link to users
);

-- Create admin user (if not exists)
INSERT INTO users (user_name, user_role)
VALUES ('Admin', 'administrator')
ON CONFLICT (user_id) DO NOTHING;