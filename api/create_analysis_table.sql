-- 创建图片分析结果表
CREATE TABLE IF NOT EXISTS image_analysis (
    id SERIAL PRIMARY KEY,
    image_id INTEGER NOT NULL,
    shap_data JSONB NOT NULL,
    ai_story JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed',
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    UNIQUE(image_id)
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_image_analysis_image_id ON image_analysis(image_id);
CREATE INDEX IF NOT EXISTS idx_image_analysis_generated_at ON image_analysis(generated_at);
CREATE INDEX IF NOT EXISTS idx_image_analysis_status ON image_analysis(status);

-- 创建更新时间戳的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_image_analysis_updated_at 
    BEFORE UPDATE ON image_analysis 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 添加注释
COMMENT ON TABLE image_analysis IS '图片分析结果表，存储SHAP分析和AI故事';
COMMENT ON COLUMN image_analysis.image_id IS '关联的图片ID';
COMMENT ON COLUMN image_analysis.shap_data IS 'SHAP分析结果，JSON格式';
COMMENT ON COLUMN image_analysis.ai_story IS 'AI生成的环境故事，JSON格式';
COMMENT ON COLUMN image_analysis.generated_at IS '分析生成时间';
COMMENT ON COLUMN image_analysis.updated_at IS '最后更新时间';
COMMENT ON COLUMN image_analysis.status IS '分析状态：processing, completed, failed'; 