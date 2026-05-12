-- PostgreSQL Database Initialization Script
-- AI Safety Layer for Women

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";  -- For geospatial queries

-- Create schemas
CREATE SCHEMA IF NOT EXISTS safety;

-- Set default schema
SET search_path TO safety, public;

-- Users table (extended)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    date_of_birth DATE,
    profile_photo_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    settings JSONB DEFAULT '{}'::jsonb
);

-- Emergency contacts table
CREATE TABLE IF NOT EXISTS emergency_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    relationship VARCHAR(100),
    priority INTEGER DEFAULT 1,
    is_verified BOOLEAN DEFAULT false,
    can_track_location BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, phone)
);

-- Locations table with PostGIS support
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accuracy FLOAT,
    altitude FLOAT,
    speed FLOAT,
    heading FLOAT,
    geom GEOMETRY(Point, 4326),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_emergency BOOLEAN DEFAULT false
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_locations_user_time ON locations(user_id, recorded_at DESC);

-- Emergency incidents table
CREATE TABLE IF NOT EXISTS emergency_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    trigger_type VARCHAR(50) NOT NULL,
    threat_level FLOAT,
    threat_types TEXT[],
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    resolution VARCHAR(50),
    notes TEXT,
    location_id UUID REFERENCES locations(id),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Evidence table
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES emergency_incidents(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    evidence_type VARCHAR(50) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    duration_seconds FLOAT,
    is_encrypted BOOLEAN DEFAULT true,
    encryption_key_id VARCHAR(255),
    cloud_backup_url TEXT,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    uploaded_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Safe zones table
CREATE TABLE IF NOT EXISTS safe_zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    zone_type VARCHAR(50) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    radius_meters FLOAT NOT NULL,
    geom GEOMETRY(Point, 4326),
    address TEXT,
    contact_phone VARCHAR(20),
    operating_hours JSONB,
    is_verified BOOLEAN DEFAULT false,
    safety_rating FLOAT DEFAULT 0,
    rating_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_safe_zones_geom ON safe_zones USING GIST(geom);

-- Guardian registrations table
CREATE TABLE IF NOT EXISTS guardians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    guardian_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    permissions JSONB DEFAULT '{"track_location": false, "receive_alerts": true}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    accepted_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, guardian_user_id)
);

-- Safety ratings table
CREATE TABLE IF NOT EXISTS safety_ratings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    lighting INTEGER CHECK (lighting >= 1 AND lighting <= 5),
    crowd_level INTEGER CHECK (crowd_level >= 1 AND crowd_level <= 5),
    safety_features TEXT[],
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_safety_ratings_geom ON safety_ratings USING GIST(geom);

-- Incident reports table
CREATE TABLE IF NOT EXISTS incident_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    incident_type VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326),
    description TEXT,
    severity VARCHAR(20) DEFAULT 'medium',
    occurred_at TIMESTAMP WITH TIME ZONE,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    is_anonymous BOOLEAN DEFAULT false,
    status VARCHAR(50) DEFAULT 'reported',
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_incident_reports_geom ON incident_reports USING GIST(geom);

-- Device tokens for push notifications
CREATE TABLE IF NOT EXISTS device_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    device_type VARCHAR(50),
    device_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, token)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Function to update geom column from lat/lon
CREATE OR REPLACE FUNCTION update_geom_from_coords()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers to automatically update geom columns
CREATE TRIGGER trigger_locations_geom
    BEFORE INSERT OR UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION update_geom_from_coords();

CREATE TRIGGER trigger_safe_zones_geom
    BEFORE INSERT OR UPDATE ON safe_zones
    FOR EACH ROW EXECUTE FUNCTION update_geom_from_coords();

CREATE TRIGGER trigger_safety_ratings_geom
    BEFORE INSERT OR UPDATE ON safety_ratings
    FOR EACH ROW EXECUTE FUNCTION update_geom_from_coords();

CREATE TRIGGER trigger_incident_reports_geom
    BEFORE INSERT OR UPDATE ON incident_reports
    FOR EACH ROW EXECUTE FUNCTION update_geom_from_coords();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_emergency_contacts_updated_at
    BEFORE UPDATE ON emergency_contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_safe_zones_updated_at
    BEFORE UPDATE ON safe_zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some default safe zone types
INSERT INTO safe_zones (name, zone_type, latitude, longitude, radius_meters, is_verified, safety_rating)
VALUES 
    ('Police Station Template', 'police_station', 0, 0, 100, true, 5.0),
    ('Hospital Template', 'hospital', 0, 0, 150, true, 5.0),
    ('Fire Station Template', 'fire_station', 0, 0, 100, true, 5.0)
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust based on your user setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA safety TO safety_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA safety TO safety_user;

COMMENT ON TABLE users IS 'User accounts for the safety application';
COMMENT ON TABLE emergency_contacts IS 'Emergency contacts for each user';
COMMENT ON TABLE emergency_incidents IS 'Records of emergency incidents';
COMMENT ON TABLE evidence IS 'Evidence files captured during emergencies';
COMMENT ON TABLE safe_zones IS 'Community-marked and verified safe locations';
COMMENT ON TABLE guardians IS 'Guardian relationships between users';
