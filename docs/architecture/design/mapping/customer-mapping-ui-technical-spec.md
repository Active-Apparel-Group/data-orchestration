# Customer Mapping UI Technical Specification

## Data Model Specification

### Core Customer Interface
```typescript
interface Customer {
  canonical: string;                    // Primary identifier
  status: CustomerStatus;               // 'review' | 'approved'
  packed_products: string;              // Data source reference
  shipped: string;                      // Data source reference
  master_order_list: string | string[]; // Single source or array
  mon_customer_ms: string;              // Monitoring system reference
  aliases: string[];                    // Alternative names
  matching_config?: MatchingConfig;     // Optional advanced configuration
  
  // Metadata (not in YAML)
  id?: string;                          // Generated UUID for UI operations
  lastModified?: Date;                  // Change tracking
  createdBy?: string;                   // User tracking
  validationErrors?: ValidationError[]; // Current validation state
}

enum CustomerStatus {
  REVIEW = 'review',
  APPROVED = 'approved'
}

interface MatchingConfig {
  style_match_strategy: StyleMatchStrategy;
  preferred_po_field?: PoField;
  style_field_override?: string;
  fuzzy_threshold?: number;             // 0-100
  size_aliases?: Record<string, string[]>;
  exact_match_fields?: string[];
  fuzzy_match_fields?: string[];
}

enum StyleMatchStrategy {
  STANDARD = 'standard',
  ALIAS_RELATED_ITEM = 'alias_related_item'
}

enum PoField {
  CUSTOMER_PO = 'Customer_PO',
  CUSTOMER_ALT_PO = 'Customer_Alt_PO'
}
```

### Validation Schema
```typescript
interface ValidationError {
  field: string;
  type: ValidationErrorType;
  message: string;
  severity: 'error' | 'warning' | 'info';
  suggestion?: string;
}

enum ValidationErrorType {
  REQUIRED_FIELD = 'required_field',
  INVALID_FORMAT = 'invalid_format',
  DUPLICATE_VALUE = 'duplicate_value',
  CIRCULAR_REFERENCE = 'circular_reference',
  UNKNOWN_DATA_SOURCE = 'unknown_data_source',
  INVALID_RANGE = 'invalid_range'
}

interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}
```

### Configuration Management
```typescript
interface AppConfig {
  dataFile: string;                     // Path to customer_mapping.yaml
  backupDirectory: string;              // Backup location
  autoSave: boolean;                    // Enable auto-save
  autoSaveInterval: number;             // Milliseconds
  maxBackups: number;                   // Backup retention count
  theme: 'light' | 'dark' | 'system';
  validation: {
    realTime: boolean;                  // Real-time vs on-save validation
    strictMode: boolean;                // Strict business rule enforcement
  };
}

interface DataSource {
  name: string;
  type: 'packed_products' | 'shipped' | 'master_order_list' | 'mon_customer_ms';
  description?: string;
  isActive: boolean;
  lastSeen?: Date;
}
```

## API Design (IPC Communication)

### File Operations
```typescript
// Main Process → Renderer Process
interface FileAPI {
  loadCustomers(): Promise<Customer[]>;
  saveCustomers(customers: Customer[]): Promise<void>;
  backupFile(): Promise<string>;        // Returns backup file path
  restoreFromBackup(backupPath: string): Promise<void>;
  validateFile(filePath: string): Promise<ValidationResult>;
  watchFileChanges(): void;             // Start file system watcher
  stopWatchingFiles(): void;
}

// IPC Channel Events
const IPC_CHANNELS = {
  FILE_LOAD_CUSTOMERS: 'file:load-customers',
  FILE_SAVE_CUSTOMERS: 'file:save-customers',
  FILE_BACKUP: 'file:backup',
  FILE_RESTORE: 'file:restore',
  FILE_VALIDATE: 'file:validate',
  FILE_CHANGED: 'file:changed',          // External file change notification
  FILE_WATCH_START: 'file:watch-start',
  FILE_WATCH_STOP: 'file:watch-stop'
} as const;
```

### Customer Operations
```typescript
interface CustomerAPI {
  createCustomer(customer: Partial<Customer>): Promise<Customer>;
  updateCustomer(id: string, updates: Partial<Customer>): Promise<Customer>;
  deleteCustomer(id: string): Promise<void>;
  duplicateCustomer(id: string, newCanonical: string): Promise<Customer>;
  validateCustomer(customer: Customer): Promise<ValidationResult>;
  searchCustomers(query: string): Promise<Customer[]>;
  getCustomersByStatus(status: CustomerStatus): Promise<Customer[]>;
}
```

### Migration and Bulk Operations
```typescript
interface MigrationAPI {
  analyzeUpgradeNeeds(): Promise<UpgradeAnalysis>;
  previewUpgrade(customerIds: string[]): Promise<UpgradePreview>;
  executeUpgrade(customerIds: string[], config: UpgradeConfig): Promise<UpgradeResult>;
  rollbackUpgrade(operationId: string): Promise<void>;
  
  importCustomersFromCSV(filePath: string): Promise<ImportResult>;
  exportCustomersToCSV(customerIds: string[], filePath: string): Promise<void>;
  applyTemplate(templateId: string, customerIds: string[]): Promise<void>;
}

interface UpgradeAnalysis {
  totalCustomers: number;
  needsUpgrade: number;
  hasMatchingConfig: number;
  recommendations: UpgradeRecommendation[];
}

interface UpgradeRecommendation {
  canonical: string;
  currentStrategy?: string;
  recommendedStrategy: string;
  reason: string;
  confidence: number;
}

interface UpgradeConfig {
  defaultStrategy: StyleMatchStrategy;
  preserveExisting: boolean;
  addBlankFields: boolean;
  customRules: Record<string, Partial<MatchingConfig>>;
}
```

## Component Architecture

### Main Application Structure
```typescript
// App.tsx - Root component
function App() {
  return (
    <ThemeProvider>
      <ErrorBoundary>
        <CustomerProvider>
          <Router>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/customers" element={<CustomerList />} />
                <Route path="/customers/:id" element={<CustomerDetail />} />
                <Route path="/templates" element={<Templates />} />
                <Route path="/tools" element={<Tools />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </AppLayout>
          </Router>
        </CustomerProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}
```

### Context Providers
```typescript
interface CustomerContextValue {
  customers: Customer[];
  loading: boolean;
  error: string | null;
  
  // CRUD operations
  createCustomer: (customer: Partial<Customer>) => Promise<void>;
  updateCustomer: (id: string, updates: Partial<Customer>) => Promise<void>;
  deleteCustomer: (id: string) => Promise<void>;
  
  // Bulk operations
  selectCustomers: (ids: string[]) => void;
  selectedCustomers: string[];
  
  // Search and filter
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  statusFilter: CustomerStatus | 'all';
  setStatusFilter: (status: CustomerStatus | 'all') => void;
  
  // Validation
  validateAll: () => Promise<ValidationResult[]>;
  getValidationErrors: (id: string) => ValidationError[];
}

interface AppContextValue {
  config: AppConfig;
  updateConfig: (updates: Partial<AppConfig>) => void;
  
  // File operations
  saveFile: () => Promise<void>;
  createBackup: () => Promise<void>;
  
  // UI state
  isDarkMode: boolean;
  toggleTheme: () => void;
  
  // Notifications
  showNotification: (message: string, type: 'success' | 'error' | 'warning') => void;
}
```

### Key Components Specification

#### CustomerList Component
```typescript
interface CustomerListProps {
  onCustomerSelect?: (customer: Customer) => void;
  selectionMode?: 'single' | 'multiple' | 'none';
  filters?: {
    status?: CustomerStatus[];
    hasMatchingConfig?: boolean;
    dataSources?: string[];
  };
}

interface CustomerListState {
  sortField: keyof Customer;
  sortDirection: 'asc' | 'desc';
  pageSize: number;
  currentPage: number;
  expandedRows: string[];
}
```

#### CustomerForm Component
```typescript
interface CustomerFormProps {
  customer?: Customer;                  // undefined for new customer
  mode: 'create' | 'edit' | 'view';
  onSave: (customer: Customer) => Promise<void>;
  onCancel: () => void;
  autoSave?: boolean;
}

interface CustomerFormState {
  formData: Customer;
  isDirty: boolean;
  validationErrors: ValidationError[];
  activeTab: 'basic' | 'datasources' | 'matching' | 'advanced';
}
```

#### MatchingConfigEditor Component
```typescript
interface MatchingConfigEditorProps {
  config?: MatchingConfig;
  onChange: (config: MatchingConfig) => void;
  customer: Customer;                   // For context-aware validation
  disabled?: boolean;
}

interface MatchingConfigEditorState {
  strategy: StyleMatchStrategy;
  showAdvanced: boolean;
  previewMode: boolean;
  previewData?: any[];
}
```

## State Management Strategy

### React Context + Custom Hooks Pattern
```typescript
// Custom hooks for specific functionality
function useCustomers() {
  const context = useContext(CustomerContext);
  if (!context) throw new Error('useCustomers must be used within CustomerProvider');
  return context;
}

function useCustomerValidation(customer: Customer) {
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [isValidating, setIsValidating] = useState(false);
  
  const validate = useCallback(async () => {
    setIsValidating(true);
    try {
      const result = await window.customerAPI.validateCustomer(customer);
      setErrors(result.errors);
      return result;
    } finally {
      setIsValidating(false);
    }
  }, [customer]);
  
  return { errors, isValidating, validate };
}

function useFileOperations() {
  const { showNotification } = useApp();
  
  const saveWithBackup = useCallback(async (customers: Customer[]) => {
    try {
      await window.fileAPI.backupFile();
      await window.fileAPI.saveCustomers(customers);
      showNotification('File saved successfully', 'success');
    } catch (error) {
      showNotification(`Save failed: ${error.message}`, 'error');
      throw error;
    }
  }, [showNotification]);
  
  return { saveWithBackup };
}
```

## Error Handling Strategy

### Error Boundaries
```typescript
class CustomerErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Customer operation error:', error, errorInfo);
    // Send to error reporting service
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }
    
    return this.props.children;
  }
}
```

### IPC Error Handling
```typescript
// Main process error handling
ipcMain.handle('file:save-customers', async (event, customers: Customer[]) => {
  try {
    await saveCustomersToFile(customers);
    return { success: true };
  } catch (error) {
    console.error('Save failed:', error);
    return {
      success: false,
      error: {
        code: error.code || 'UNKNOWN_ERROR',
        message: error.message,
        details: error.stack
      }
    };
  }
});

// Renderer process error handling
async function saveCustomers(customers: Customer[]) {
  const result = await window.customerAPI.saveCustomers(customers);
  if (!result.success) {
    throw new Error(`Save failed: ${result.error.message}`);
  }
}
```

## Performance Considerations

### Large Dataset Handling
```typescript
// Virtual scrolling for customer list
function VirtualizedCustomerList({ customers }: { customers: Customer[] }) {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 });
  
  const visibleCustomers = useMemo(() => 
    customers.slice(visibleRange.start, visibleRange.end),
    [customers, visibleRange]
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={customers.length}
      itemSize={80}
      onItemsRendered={({ visibleStartIndex, visibleStopIndex }) =>
        setVisibleRange({ start: visibleStartIndex, end: visibleStopIndex })
      }
    >
      {({ index, style }) => (
        <div style={style}>
          <CustomerRow customer={customers[index]} />
        </div>
      )}
    </FixedSizeList>
  );
}
```

### Debounced Operations
```typescript
// Debounced search and validation
function useDebounceCustomerSearch(delay = 300) {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [searchQuery, delay]);
  
  return { searchQuery, setSearchQuery, debouncedQuery };
}
```

---

**Document Version**: 1.0  
**Last Updated**: June 3, 2025  
**Review Status**: Draft  
**Technical Owner**: Development Team
