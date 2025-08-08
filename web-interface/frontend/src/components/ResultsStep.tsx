/**
 * Results Step Component
 * Purpose: Display upload results and export options
 * Author: Data Engineering Team
 * Date: August 8, 2025
 */

import React from 'react';
import { Box, Typography, Button } from '@mui/material';

interface ResultsStepProps {
  uploadResult: any;
  onReset: () => void;
  onError: (error: string) => void;
}

const ResultsStep: React.FC<ResultsStepProps> = ({
  uploadResult,
  onReset,
  onError,
}) => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        ✅ Upload Complete
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Your data has been successfully uploaded to Monday.com.
      </Typography>
      
      {/* Placeholder content */}
      <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, my: 2 }}>
        <Typography variant="body2">
          Results and export interface will be implemented here.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="contained" onClick={onReset}>
          Upload Another File
        </Button>
      </Box>
    </Box>
  );
};

export default ResultsStep;
