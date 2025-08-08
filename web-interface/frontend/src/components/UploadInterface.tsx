/**
 * Upload Interface Component
 * Purpose: Main interface for file upload, column mapping, and progress tracking
 * Author: Data Engineering Team
 * Date: August 8, 2025
 */

import React, { useState, useCallback } from 'react';
import {
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Typography,
  Box,
  Alert,
  Chip,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  ViewColumn as MappingIcon,
  Upload as ProcessIcon,
  CheckCircle as CompleteIcon,
} from '@mui/icons-material';

import FileUploadStep from './FileUploadStep';
import ColumnMappingStep from './ColumnMappingStep';
import UploadProgressStep from './UploadProgressStep';
import ResultsStep from './ResultsStep';

// Types
interface FileAnalysis {
  filename: string;
  file_type?: string;
  total_rows?: number;
  detected_columns: Array<{
    name: string;
    data_type: string;
    sample_values: string[];
    null_count: number;
  }>;
  columns?: Array<{
    name: string;
    type: string;
    samples: any[];
  }>;
  sample_data?: Array<Record<string, any>>;
  preview?: Array<Record<string, any>>;
  rowCount?: number;
  qualityScore?: number;
  fileSize?: number;
}

interface ColumnMapping {
  file_column: string;
  board_column_id: string;
  board_column_title: string;
  column_type: string;
  is_mapped: boolean;
}

interface UploadProgress {
  upload_id: string;
  status: string;
  total_records: number;
  processed_records: number;
  successful_records: number;
  failed_records: number;
  progress_percentage: number;
  current_operation: string;
  errors: Array<any>;
}

interface UploadResult {
  upload_id: string;
  status: string;
  total_records: number;
  successful_records: number;
  failed_records: number;
  monday_item_ids: string[];
  errors: Array<any>;
  export_data?: any;
}

const steps = [
  {
    label: 'Upload File',
    description: 'Upload your CSV or Excel file',
    icon: <UploadIcon />,
  },
  {
    label: 'Map Columns',
    description: 'Map file columns to Monday.com board columns',
    icon: <MappingIcon />,
  },
  {
    label: 'Upload Progress',
    description: 'Monitor upload progress',
    icon: <ProcessIcon />,
  },
  {
    label: 'Results',
    description: 'View results and export data',
    icon: <CompleteIcon />,
  },
];

const UploadInterface: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [fileAnalysis, setFileAnalysis] = useState<FileAnalysis | null>(null);
  const [selectedBoard, setSelectedBoard] = useState<any>(null);
  const [columnMappings, setColumnMappings] = useState<ColumnMapping[]>([]);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleReset = () => {
    setActiveStep(0);
    setUploadedFile(null);
    setFileAnalysis(null);
    setSelectedBoard(null);
    setColumnMappings([]);
    setUploadProgress(null);
    setUploadResult(null);
    setError(null);
  };

  const handleFileUpload = useCallback((file: File, analysis: FileAnalysis) => {
    setUploadedFile(file);
    setFileAnalysis(analysis);
    setError(null);
    handleNext();
  }, []);

  const handleBoardSelection = useCallback((board: any) => {
    setSelectedBoard(board);
    setError(null);
  }, []);

  const handleColumnMapping = useCallback((mappings: ColumnMapping[]) => {
    setColumnMappings(mappings);
    setError(null);
    handleNext();
  }, []);

  const handleUploadStart = useCallback((progress: UploadProgress) => {
    setUploadProgress(progress);
    setError(null);
    handleNext();
  }, []);

  const handleUploadComplete = useCallback((result: UploadResult) => {
    setUploadResult(result);
    setError(null);
    handleNext();
  }, []);

  const handleError = useCallback((errorMessage: string) => {
    setError(errorMessage);
  }, []);

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <FileUploadStep
            onFileUpload={handleFileUpload}
            onError={handleError}
          />
        );
      case 1:
        return (
          <ColumnMappingStep
            fileAnalysis={fileAnalysis}
            selectedBoard={selectedBoard}
            onBoardSelection={handleBoardSelection}
            onColumnMapping={handleColumnMapping}
            onBack={handleBack}
            onError={handleError}
          />
        );
      case 2:
        return (
          <UploadProgressStep
            uploadedFile={uploadedFile}
            selectedBoard={selectedBoard}
            columnMappings={columnMappings}
            onUploadStart={handleUploadStart}
            onUploadComplete={handleUploadComplete}
            onBack={handleBack}
            onError={handleError}
          />
        );
      case 3:
        return (
          <ResultsStep
            uploadResult={uploadResult}
            onReset={handleReset}
            onError={handleError}
          />
        );
      default:
        return 'Unknown step';
    }
  };

  return (
    <Box sx={{ maxWidth: 800, margin: 'auto' }}>
      {/* Header */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📊 Monday.com Data Upload
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload your CSV or Excel files to Monday.com boards with intelligent column mapping
        </Typography>
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Progress Indicators */}
      {fileAnalysis && (
        <Paper elevation={1} sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label={`📁 ${fileAnalysis.filename}`}
              color="primary"
              variant="outlined"
              size="small"
            />
            <Chip
              label={`📊 ${fileAnalysis.total_rows} rows`}
              color="info"
              variant="outlined"
              size="small"
            />
            <Chip
              label={`📋 ${fileAnalysis?.detected_columns?.length || fileAnalysis?.columns?.length || 0} columns`}
              color="info"
              variant="outlined"
              size="small"
            />
            {selectedBoard && (
              <Chip
                label={`🎯 ${selectedBoard.name}`}
                color="success"
                variant="outlined"
                size="small"
              />
            )}
          </Box>
        </Paper>
      )}

      {/* Main Stepper */}
      <Paper elevation={2}>
        <Stepper activeStep={activeStep} orientation="vertical">
          {steps.map((step, index) => (
            <Step key={step.label}>
              <StepLabel
                optional={
                  index === steps.length - 1 ? (
                    <Typography variant="caption">Last step</Typography>
                  ) : null
                }
                StepIconComponent={() => (
                  <Box
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      backgroundColor:
                        activeStep >= index ? 'primary.main' : 'grey.300',
                      color: activeStep >= index ? 'white' : 'grey.600',
                    }}
                  >
                    {step.icon}
                  </Box>
                )}
              >
                <Typography variant="h6">{step.label}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {step.description}
                </Typography>
              </StepLabel>
              <StepContent>
                <Box sx={{ p: 2 }}>
                  {getStepContent(index)}
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>
    </Box>
  );
};

export default UploadInterface;
