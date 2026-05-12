// MongoDB Initialization Script
// AI Safety Layer for Women - Evidence & Analytics Database

// Switch to the safety evidence database
db = db.getSiblingDB('safety_evidence');

// Create collections with validation schemas

// Evidence collection - stores evidence metadata and raw data
db.createCollection('evidence', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['user_id', 'incident_id', 'type', 'created_at'],
            properties: {
                user_id: {
                    bsonType: 'string',
                    description: 'User UUID - required'
                },
                incident_id: {
                    bsonType: 'string',
                    description: 'Incident UUID - required'
                },
                type: {
                    enum: ['audio', 'video', 'image', 'location_log', 'sensor_data'],
                    description: 'Evidence type - required'
                },
                file_data: {
                    bsonType: 'binData',
                    description: 'Binary file data (encrypted)'
                },
                file_path: {
                    bsonType: 'string',
                    description: 'Path to file storage'
                },
                metadata: {
                    bsonType: 'object',
                    properties: {
                        duration_seconds: { bsonType: 'double' },
                        file_size_bytes: { bsonType: 'int' },
                        mime_type: { bsonType: 'string' },
                        resolution: { bsonType: 'string' },
                        sample_rate: { bsonType: 'int' }
                    }
                },
                location: {
                    bsonType: 'object',
                    properties: {
                        type: { enum: ['Point'] },
                        coordinates: {
                            bsonType: 'array',
                            items: { bsonType: 'double' }
                        }
                    }
                },
                encryption: {
                    bsonType: 'object',
                    properties: {
                        algorithm: { bsonType: 'string' },
                        key_id: { bsonType: 'string' },
                        iv: { bsonType: 'binData' }
                    }
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Creation timestamp - required'
                },
                uploaded_to_cloud: {
                    bsonType: 'bool'
                },
                cloud_url: {
                    bsonType: 'string'
                }
            }
        }
    }
});

// Create indexes for evidence collection
db.evidence.createIndex({ 'user_id': 1, 'created_at': -1 });
db.evidence.createIndex({ 'incident_id': 1 });
db.evidence.createIndex({ 'type': 1 });
db.evidence.createIndex({ 'location': '2dsphere' });
db.evidence.createIndex({ 'created_at': 1 }, { expireAfterSeconds: 7776000 }); // 90 days TTL

// AI Detection Logs - stores all AI detection events
db.createCollection('ai_detection_logs', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['user_id', 'detection_type', 'timestamp'],
            properties: {
                user_id: {
                    bsonType: 'string'
                },
                detection_type: {
                    enum: ['audio', 'visual', 'combined'],
                    description: 'Type of AI detection'
                },
                timestamp: {
                    bsonType: 'date'
                },
                audio_analysis: {
                    bsonType: 'object',
                    properties: {
                        threat_detected: { bsonType: 'bool' },
                        threat_type: { bsonType: 'string' },
                        confidence: { bsonType: 'double' },
                        features: { bsonType: 'object' }
                    }
                },
                visual_analysis: {
                    bsonType: 'object',
                    properties: {
                        threat_detected: { bsonType: 'bool' },
                        detections: { bsonType: 'array' },
                        pose_analysis: { bsonType: 'object' },
                        frame_metadata: { bsonType: 'object' }
                    }
                },
                risk_assessment: {
                    bsonType: 'object',
                    properties: {
                        overall_risk: { bsonType: 'double' },
                        risk_factors: { bsonType: 'array' },
                        risk_level: { bsonType: 'string' }
                    }
                },
                location: {
                    bsonType: 'object',
                    properties: {
                        type: { enum: ['Point'] },
                        coordinates: { bsonType: 'array' }
                    }
                },
                triggered_emergency: {
                    bsonType: 'bool'
                },
                processing_time_ms: {
                    bsonType: 'double'
                }
            }
        }
    }
});

// Indexes for AI detection logs
db.ai_detection_logs.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.ai_detection_logs.createIndex({ 'detection_type': 1, 'timestamp': -1 });
db.ai_detection_logs.createIndex({ 'triggered_emergency': 1 });
db.ai_detection_logs.createIndex({ 'location': '2dsphere' });
db.ai_detection_logs.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 2592000 }); // 30 days TTL

// Location History - high-frequency location tracking
db.createCollection('location_history', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['user_id', 'location', 'timestamp'],
            properties: {
                user_id: {
                    bsonType: 'string'
                },
                location: {
                    bsonType: 'object',
                    required: ['type', 'coordinates'],
                    properties: {
                        type: { enum: ['Point'] },
                        coordinates: { bsonType: 'array' }
                    }
                },
                timestamp: {
                    bsonType: 'date'
                },
                accuracy: {
                    bsonType: 'double'
                },
                altitude: {
                    bsonType: 'double'
                },
                speed: {
                    bsonType: 'double'
                },
                heading: {
                    bsonType: 'double'
                },
                is_emergency: {
                    bsonType: 'bool'
                },
                battery_level: {
                    bsonType: 'int'
                }
            }
        }
    }
});

// Time-series optimized indexes for location
db.location_history.createIndex({ 'user_id': 1, 'timestamp': -1 });
db.location_history.createIndex({ 'location': '2dsphere' });
db.location_history.createIndex({ 'is_emergency': 1, 'timestamp': -1 });
db.location_history.createIndex({ 'timestamp': 1 }, { expireAfterSeconds: 604800 }); // 7 days TTL

// Crime Statistics - aggregated crime data
db.createCollection('crime_statistics', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['location', 'crime_type', 'count'],
            properties: {
                location: {
                    bsonType: 'object',
                    properties: {
                        type: { enum: ['Point'] },
                        coordinates: { bsonType: 'array' }
                    }
                },
                area_name: {
                    bsonType: 'string'
                },
                crime_type: {
                    bsonType: 'string'
                },
                count: {
                    bsonType: 'int'
                },
                time_period: {
                    bsonType: 'string'
                },
                severity_score: {
                    bsonType: 'double'
                },
                last_updated: {
                    bsonType: 'date'
                },
                source: {
                    bsonType: 'string'
                }
            }
        }
    }
});

db.crime_statistics.createIndex({ 'location': '2dsphere' });
db.crime_statistics.createIndex({ 'crime_type': 1 });
db.crime_statistics.createIndex({ 'area_name': 1 });

// User Analytics - aggregated user behavior
db.createCollection('user_analytics', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['user_id', 'date'],
            properties: {
                user_id: {
                    bsonType: 'string'
                },
                date: {
                    bsonType: 'date'
                },
                app_opens: {
                    bsonType: 'int'
                },
                sos_triggers: {
                    bsonType: 'int'
                },
                fake_calls_used: {
                    bsonType: 'int'
                },
                safe_routes_requested: {
                    bsonType: 'int'
                },
                locations_shared: {
                    bsonType: 'int'
                },
                high_risk_alerts: {
                    bsonType: 'int'
                },
                most_visited_locations: {
                    bsonType: 'array'
                },
                active_hours: {
                    bsonType: 'array'
                }
            }
        }
    }
});

db.user_analytics.createIndex({ 'user_id': 1, 'date': -1 });
db.user_analytics.createIndex({ 'date': 1 }, { expireAfterSeconds: 31536000 }); // 1 year TTL

// System Logs - application logs
db.createCollection('system_logs', {
    capped: true,
    size: 1073741824, // 1GB
    max: 1000000 // Max 1M documents
});

db.system_logs.createIndex({ 'timestamp': -1 });
db.system_logs.createIndex({ 'level': 1, 'timestamp': -1 });
db.system_logs.createIndex({ 'service': 1 });

// Create a read-only user for analytics
db.createUser({
    user: 'analytics_reader',
    pwd: 'analytics_password', // Change in production
    roles: [
        { role: 'read', db: 'safety_evidence' }
    ]
});

// Print summary
print('MongoDB initialization complete!');
print('Collections created: evidence, ai_detection_logs, location_history, crime_statistics, user_analytics, system_logs');
print('Indexes created for geospatial queries and time-series data');
