-- Health Predictor System Database v2
-- Khởi tạo database cho hệ thống dự đoán sức khỏe với ML

-- Tạo bảng người dùng hệ thống
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10), -- male, female, other
    phone VARCHAR(20),
    address TEXT,
    
    -- Thông tin riêng cho người bệnh
    current_latitude DECIMAL(10, 8), -- Vị trí hiện tại - chỉ cho patient
    current_longitude DECIMAL(11, 8), -- Vị trí hiện tại - chỉ cho patient
    current_diseases TEXT, -- Bệnh đang mắc - JSON array of disease IDs
    
    -- Thông tin chung
    role VARCHAR(20) NOT NULL CHECK (role IN ('doctor', 'patient', 'admin')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index cho bảng users
CREATE INDEX IF NOT EXISTS idx_users_name ON users(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_user_location ON users(current_latitude, current_longitude);

-- Tạo bảng các triệu chứng
CREATE TABLE IF NOT EXISTS symptoms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE, -- Mã triệu chứng
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index cho bảng symptoms
CREATE INDEX IF NOT EXISTS idx_symptoms_code ON symptoms(code);

-- Tạo bảng các loại bệnh
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE, -- ICD-10 hoặc mã tự định nghĩa
    description TEXT,
    
    -- Thông tin về khả năng lây truyền
    is_contagious BOOLEAN DEFAULT FALSE NOT NULL, -- Có lây truyền không
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tạo index cho bảng diseases
CREATE INDEX IF NOT EXISTS idx_diseases_name ON diseases(name);
CREATE INDEX IF NOT EXISTS idx_diseases_code ON diseases(code);
CREATE INDEX IF NOT EXISTS idx_diseases_contagious ON diseases(is_contagious);

-- Tạo bảng lịch sử bệnh án
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Người bệnh
    doctor_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Bác sĩ chẩn đoán (null nếu là hệ thống)
    
    -- Phân loại
    record_type VARCHAR(20) NOT NULL CHECK (record_type IN ('doctor_diagnosis', 'system_prediction')),
    confidence_score DECIMAL(5,4), -- Độ tin cậy (chỉ cho system_prediction)
    
    -- Trạng thái
    status VARCHAR(50), -- new, completed
    
    -- Đánh giá độ chính xác
    is_accurate BOOLEAN, -- Có chính xác hay không (đánh giá sau khi có kết quả thực tế)
    
    -- Điều kiện môi trường
    weather_temp DECIMAL(5,2), -- Nhiệt độ thời tiết (°C)
    humidity INTEGER, -- Độ ẩm (%)
    air_quality_index INTEGER, -- Chỉ số chất lượng không khí
    season VARCHAR(20), -- spring, summer, autumn, winter
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    create_by INTEGER,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_by INTEGER
);

-- Tạo index cho bảng medical_records
CREATE INDEX IF NOT EXISTS idx_medical_records_user ON medical_records(user_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_doctor ON medical_records(doctor_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_type ON medical_records(record_type);
CREATE INDEX IF NOT EXISTS idx_medical_records_created ON medical_records(created_at);

-- Tạo bảng triệu chứng trong từng bệnh án (many-to-many)
CREATE TABLE IF NOT EXISTS record_symptoms (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
    symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
    
    UNIQUE(record_id, symptom_id)
);

-- Tạo index cho bảng record_symptoms
CREATE INDEX IF NOT EXISTS idx_record_symptoms_symptom ON record_symptoms(symptom_id);

-- Tạo bảng bệnh được chẩn đoán trong từng bệnh án (many-to-many)
CREATE TABLE IF NOT EXISTS record_diseases (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
    disease_id INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    
    -- Tỉ lệ mắc bệnh
    probability DECIMAL(5,4), -- Tỉ lệ/xác suất mắc bệnh (0.0000 - 1.0000)
    
    UNIQUE(record_id, disease_id)
);

-- Tạo index cho bảng record_diseases
CREATE INDEX IF NOT EXISTS idx_record_diseases_disease ON record_diseases(disease_id);

-- Tạo bảng lịch sử train model
CREATE TABLE IF NOT EXISTS model_training_history (
    id SERIAL PRIMARY KEY,
    trigger_type VARCHAR(30), -- doctor_session_end, user_feedback
    triggered_by INTEGER REFERENCES users(id) ON DELETE SET NULL, -- User trigger training
    
    -- Dữ liệu training
    training_data_count INTEGER, -- Số lượng bản ghi dùng để train
    doctor_diagnosed_count INTEGER, -- Số bản ghi do bác sĩ chẩn đoán
    system_predicted_count INTEGER, -- Số bản ghi do hệ thống dự đoán
    
    deployed_at TIMESTAMP,
    
    -- Thời gian
    training_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_completed_at TIMESTAMP,
    training_duration_seconds INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    notes TEXT
);

-- Tạo index cho bảng model_training_history
CREATE INDEX IF NOT EXISTS idx_training_trigger ON model_training_history(trigger_type);
CREATE INDEX IF NOT EXISTS idx_training_user ON model_training_history(triggered_by);
CREATE INDEX IF NOT EXISTS idx_training_started ON model_training_history(training_started_at);
CREATE INDEX IF NOT EXISTS idx_training_status ON model_training_history(status);

-- Tạo bảng phiên làm việc của bác sĩ
CREATE TABLE IF NOT EXISTS doctor_sessions (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    
    -- Thống kê phiên làm việc
    total_records_created INTEGER DEFAULT 0,
    total_diagnoses_made INTEGER DEFAULT 0,
    total_patients_seen INTEGER DEFAULT 0,
    
    -- Trigger training
    auto_train_triggered BOOLEAN DEFAULT FALSE,
    training_id INTEGER REFERENCES model_training_history(id) ON DELETE SET NULL,
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'interrupted')),
    notes TEXT
);

-- Tạo index cho bảng doctor_sessions
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_doctor ON doctor_sessions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_start ON doctor_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_end ON doctor_sessions(session_end);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_status ON doctor_sessions(status);

-- Insert dữ liệu mẫu cho bảng users
INSERT INTO users (username, email, password_hash, first_name, last_name, role) VALUES
('admin', 'admin@healthpredictor.com', '$2b$12$example_hash', 'System', 'Admin', 'admin'),
('dr_nguyen', 'dr.nguyen@hospital.com', '$2b$12$example_hash', 'Văn Minh', 'Nguyễn', 'doctor'),
('dr_tran', 'dr.tran@hospital.com', '$2b$12$example_hash', 'Thị Hoa', 'Trần', 'doctor'),
('patient_001', 'patient001@email.com', '$2b$12$example_hash', 'Minh', 'Lê', 'patient'),
('patient_002', 'patient002@email.com', '$2b$12$example_hash', 'Thu', 'Phạm', 'patient')
ON CONFLICT (username) DO NOTHING;

-- Insert dữ liệu mẫu cho bảng symptoms
INSERT INTO symptoms (name, code, description) VALUES
('Sốt', 'FEVER', 'Nhiệt độ cơ thể cao hơn bình thường'),
('Ho', 'COUGH', 'Phản xạ đẩy không khí ra khỏi phổi'),
('Đau đầu', 'HEADACHE', 'Cảm giác đau ở vùng đầu'),
('Đau họng', 'SORE_THROAT', 'Cảm giác đau, ngứa ở cổ họng'),
('Sổ mũi', 'RUNNY_NOSE', 'Tiết dịch mũi nhiều'),
('Mệt mỏi', 'FATIGUE', 'Cảm giác thiếu năng lượng'),
('Đau nhức cơ thể', 'BODY_ACHES', 'Đau nhức ở các cơ bắp'),
('Buồn nôn', 'NAUSEA', 'Cảm giác muốn nôn'),
('Tiêu chảy', 'DIARRHEA', 'Đi ngoài phân lỏng'),
('Khó thở', 'SHORTNESS_OF_BREATH', 'Cảm giác thiếu không khí')
ON CONFLICT (name) DO NOTHING;

-- Insert dữ liệu mẫu cho bảng diseases
INSERT INTO diseases (name, code, description, is_contagious) VALUES
('Cảm lạnh thông thường', 'COMMON_COLD', 'Nhiễm trùng đường hô hấp trên do virus', TRUE),
('Cúm mùa', 'SEASONAL_FLU', 'Nhiễm trùng do virus cúm', TRUE),
('Viêm dạ dày ruột', 'GASTROENTERITIS', 'Viêm dạ dày và ruột non', TRUE),
('Dị ứng thời tiết', 'ALLERGIC_RHINITIS', 'Phản ứng dị ứng với các chất trong không khí', FALSE),
('Sốc nhiệt', 'HEAT_EXHAUSTION', 'Tình trạng cơ thể quá nóng', FALSE),
('Khỏe mạnh', 'HEALTHY', 'Không có triệu chứng bệnh lý', FALSE),
('COVID-19', 'COVID19', 'Bệnh do virus SARS-CoV-2', TRUE),
('Viêm họng', 'PHARYNGITIS', 'Viêm niêm mạc họng', TRUE),
('Cao huyết áp', 'HYPERTENSION', 'Huyết áp cao', FALSE),
('Tiểu đường type 2', 'DIABETES_T2', 'Rối loạn chuyển hóa glucose', FALSE)
ON CONFLICT (name) DO NOTHING;

-- Insert dữ liệu mẫu cho medical_records
WITH sample_users AS (
    SELECT id, role FROM users WHERE role = 'patient' LIMIT 2
),
sample_doctors AS (
    SELECT id FROM users WHERE role = 'doctor' LIMIT 1
)
INSERT INTO medical_records (
    user_id, doctor_id, record_type, confidence_score, status, 
    weather_temp, humidity, air_quality_index, season,
    created_at
)
SELECT 
    u.id,
    d.id,
    'doctor_diagnosis',
    NULL,
    'completed',
    CASE 
        WHEN random() < 0.3 THEN 15 + random() * 10  -- Winter/Spring
        WHEN random() < 0.6 THEN 25 + random() * 10  -- Summer
        ELSE 20 + random() * 8                       -- Autumn
    END,
    50 + (random() * 40)::INTEGER,
    1 + (random() * 4)::INTEGER,
    CASE 
        WHEN random() < 0.25 THEN 'spring'
        WHEN random() < 0.5 THEN 'summer'
        WHEN random() < 0.75 THEN 'autumn'
        ELSE 'winter'
    END,
    CURRENT_TIMESTAMP - (random() * INTERVAL '30 days')
FROM sample_users u
CROSS JOIN sample_doctors d
LIMIT 5;

-- Grant permissions cho user database
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO health_predictor_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO health_predictor_user;
GRANT USAGE ON SCHEMA public TO health_predictor_user;

-- Tạo function để tự động update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Tạo trigger cho các bảng có updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_symptoms_updated_at BEFORE UPDATE ON symptoms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_diseases_updated_at BEFORE UPDATE ON diseases 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_medical_records_updated_at BEFORE UPDATE ON medical_records 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Tạo view để xem thống kê
CREATE OR REPLACE VIEW medical_records_summary AS
SELECT 
    mr.id,
    CONCAT(u.first_name, ' ', u.last_name) AS patient_name,
    CASE 
        WHEN mr.doctor_id IS NOT NULL THEN CONCAT(d.first_name, ' ', d.last_name)
        ELSE 'Hệ thống'
    END AS diagnosed_by,
    mr.record_type,
    mr.confidence_score,
    mr.status,
    mr.is_accurate,
    mr.created_at,
    COUNT(rs.symptom_id) AS symptom_count,
    COUNT(rd.disease_id) AS disease_count
FROM medical_records mr
LEFT JOIN users u ON mr.user_id = u.id
LEFT JOIN users d ON mr.doctor_id = d.id
LEFT JOIN record_symptoms rs ON mr.id = rs.record_id
LEFT JOIN record_diseases rd ON mr.id = rd.record_id
GROUP BY mr.id, u.first_name, u.last_name, d.first_name, d.last_name, 
         mr.record_type, mr.confidence_score, mr.status, mr.is_accurate, mr.created_at;

-- Comment cho các bảng
COMMENT ON TABLE users IS 'Bảng quản lý người dùng: bác sĩ, người bệnh, admin';
COMMENT ON TABLE symptoms IS 'Danh mục các triệu chứng có thể theo dõi';
COMMENT ON TABLE diseases IS 'Danh mục các loại bệnh với thông tin lây truyền';
COMMENT ON TABLE medical_records IS 'Lịch sử bệnh án - do bác sĩ hoặc hệ thống chuẩn đoán';
COMMENT ON TABLE record_symptoms IS 'Triệu chứng cụ thể trong từng bệnh án';
COMMENT ON TABLE record_diseases IS 'Bệnh được chẩn đoán trong từng bệnh án';
COMMENT ON TABLE model_training_history IS 'Lịch sử train model sau mỗi phiên bác sĩ hoặc theo lịch';
COMMENT ON TABLE doctor_sessions IS 'Phiên làm việc của bác sĩ - trigger train model khi kết thúc'; 