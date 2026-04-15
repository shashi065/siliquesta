-- Database schema for SILIQUESTA

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    plan VARCHAR(50) DEFAULT 'FREE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Design projects
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simulation results
CREATE TABLE IF NOT EXISTS simulations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wn FLOAT NOT NULL,
    wp FLOAT NOT NULL,
    vdd FLOAT NOT NULL,
    temp FLOAT NOT NULL,
    cl_ff FLOAT NOT NULL,
    corner VARCHAR(10),
    tech_node INTEGER,
    freq FLOAT,
    power FLOAT,
    delay FLOAT,
    fom FLOAT,
    id_n FLOAT,
    id_p FLOAT,
    vth FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_project (user_id, project_id),
    INDEX idx_created (created_at)
);

-- PVT analysis results
CREATE TABLE IF NOT EXISTS pvt_results (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER REFERENCES simulations(id) ON DELETE CASCADE,
    corner VARCHAR(10),
    temp FLOAT,
    vdd FLOAT,
    freq FLOAT,
    power FLOAT,
    delay FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Digital Twin data
CREATE TABLE IF NOT EXISTS digital_twin (
    id SERIAL PRIMARY KEY,
    simulation_id INTEGER REFERENCES simulations(id) ON DELETE CASCADE,
    years INTEGER,
    dvth_nbti FLOAT,
    did_hci FLOAT,
    mtf_em FLOAT,
    health_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI chat history
CREATE TABLE IF NOT EXISTS ai_chat_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message TEXT,
    response TEXT,
    source VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Design DNA (saved circuit knowledge)
CREATE TABLE IF NOT EXISTS design_dna (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    description TEXT,
    params JSONB,
    results JSONB,
    embedding VECTOR(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_dna (user_id),
    INDEX idx_embedding (embedding)
);

-- Create indexes for performance
CREATE INDEX idx_simulations_user ON simulations(user_id);
CREATE INDEX idx_simulations_project ON simulations(project_id);
CREATE INDEX idx_pvt_simulation ON pvt_results(simulation_id);
CREATE INDEX idx_twin_simulation ON digital_twin(simulation_id);
CREATE INDEX idx_chat_user ON ai_chat_history(user_id);
