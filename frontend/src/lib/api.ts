let BASE_URL = "http://localhost:8000/api/v1";
if (typeof window !== "undefined") {
  const host = window.location.hostname;
  BASE_URL = `http://${host}:8000/api/v1`;
}

export async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const url = `${BASE_URL}${endpoint}`;
  
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers as any,
  };
  
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function login(username: string, secret: string) {
  return fetchAPI("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password: secret }),
  });
}

export async function getMe() {
  return fetchAPI("/auth/me");
}

export async function getGlobalEngineAssets() {
  return fetchAPI("/assets/global-engine/all");
}

export async function getFleetAvailability() {
  return fetchAPI("/reporting/fleet-availability");
}

export async function getReportingMTBF() {
  return fetchAPI("/reporting/mtbf");
}

export async function getReportingMTTR() {
  return fetchAPI("/reporting/mttr");
}

export async function getOperationalTimeline() {
  return fetchAPI("/reporting/timeline");
}

export async function getServiceableComponents() {
  return fetchAPI("/components/serviceable");
}

// Fleet endpoints
export async function getFleetStatus() {
  return fetchAPI("/fleet/status");
}

export async function getAircraftList() {
  return fetchAPI("/aircraft");
}

export async function getAircraftDetails(id: string) {
  return fetchAPI(`/aircraft/${id}`);
}

export async function getAircraftComponents(id: string) {
  return fetchAPI(`/aircraft/${id}/components`);
}

export async function getAircraftTimeline(id: string) {
  return fetchAPI(`/aircraft/${id}/timeline`);
}

// Components endpoints
export async function getComponentDetails(id: string) {
  return fetchAPI(`/components/${id}`);
}

export async function getComponentHistory(id: string) {
  return fetchAPI(`/components/${id}/history`);
}

// Queue endpoints
export async function getArsenalWorkQueue() {
  return fetchAPI("/arsenal/work-queue");
}

export async function getPendingMaintenance() {
  return fetchAPI("/maintenance/pending");
}

// Transactional flow endpoints
export async function openFlight(
  aircraftId: string,
  pilotName: string,
  missionType: string,
  plannedHours: number,
  authorizedBy: string,
  copilotName?: string,
  observations?: string
) {
  return fetchAPI("/flight/open", {
    method: "POST",
    body: JSON.stringify({
      aircraft_id: aircraftId,
      pilot_name: pilotName,
      copilot_name: copilotName || null,
      mission_type: missionType,
      planned_hours: plannedHours,
      observations: observations || null,
      authorized_by: authorizedBy,
    }),
  });
}

export async function getFlightLogbook() {
  return fetchAPI("/flight/logbook");
}

export async function closeFlight(aircraftId: string, flightHours: number, technicalObservations?: string) {
  return fetchAPI("/flight/close", {
    method: "POST",
    body: JSON.stringify({ aircraft_id: aircraftId, flight_hours: flightHours, technical_observations: technicalObservations || null }),
  });
}

export async function createAirworthinessDecision(payload: {
  aircraft_id: string;
  decision_status: string;
  reason: string;
  decided_by: string;
}) {
  return fetchAPI("/airworthiness/decision", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function executeCommandConsole(payload: {
  command_type: string;
  payload: Record<string, unknown>;
}) {
  return fetchAPI("/command-console/execute", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getSecurityAuditEvents() {
  return fetchAPI("/security/audit-events");
}

export async function getTechnicians() {
  return fetchAPI("/personnel/technicians");
}

export async function getProvisionRequests() {
  return fetchAPI("/procurement/provision-requests");
}

export async function reportFailure(aircraftId: string, componentId: string, failureCode: string, severity: string, description: string, reportedBy: string) {
  return fetchAPI("/maintenance/report-failure", {
    method: "POST",
    body: JSON.stringify({
      aircraft_id: aircraftId,
      component_id: componentId,
      failure_code: failureCode,
      severity,
      description,
      reported_by: reportedBy,
    }),
  });
}

export async function createArsenalRequest(componentId: string, sourceSquadronId: string, failureReportId: string, requestedBy: string, priority: string) {
  return fetchAPI("/arsenal/create-request", {
    method: "POST",
    body: JSON.stringify({
      component_asset_id: componentId,
      source_squadron_id: sourceSquadronId,
      failure_report_id: failureReportId,
      requested_by: requestedBy,
      priority,
    }),
  });
}

export async function removeComponent(aircraftId: string, componentId: string, removedBy: string) {
  return fetchAPI("/squadron/remove-component", {
    method: "POST",
    body: JSON.stringify({
      aircraft_id: aircraftId,
      component_id: componentId,
      removed_by: removedBy,
    }),
  });
}

export async function transferToSquadronStorage(componentId: string, destinationDepartmentId: string, performedBy: string) {
  return fetchAPI("/supply-chain/transfer-to-squadron-storage", {
    method: "POST",
    body: JSON.stringify({
      component_id: componentId,
      destination_department_id: destinationDepartmentId,
      performed_by: performedBy,
    }),
  });
}

export async function receiveComponent(
  componentId: string,
  maintenanceRequestId: string,
  receivedByDepartmentId: string,
  conditionNotes: string,
  documentationComplete: boolean,
  failureReportCode: string,
  maintenanceActionFormCode: string,
  workOrderCode: string
) {
  return fetchAPI("/arsenal/receive-component", {
    method: "POST",
    body: JSON.stringify({
      component_id: componentId,
      maintenance_request_id: maintenanceRequestId,
      received_by_department_id: receivedByDepartmentId,
      condition_notes: conditionNotes,
      documentation_complete: documentationComplete,
      failure_report_code: failureReportCode,
      maintenance_action_form_code: maintenanceActionFormCode,
      work_order_code: workOrderCode,
    }),
  });
}

export async function createReview(maintenanceRequestId: string, engineerId: string, failureAnalysis: string, repairable: boolean, recommendedAction: string, instructionCode: string, procedureDescription: string) {
  return fetchAPI("/engineering/create-review", {
    method: "POST",
    body: JSON.stringify({
      maintenance_request_id: maintenanceRequestId,
      engineer_id: engineerId,
      failure_analysis: failureAnalysis,
      repairable,
      recommended_action: recommendedAction,
      instruction_code: instructionCode,
      procedure_description: procedureDescription,
    }),
  });
}

export async function getEngineeringQueue() {
  return fetchAPI("/engineering/queue");
}

export async function getEngineeringReviewContext(maintenanceRequestId: string) {
  return fetchAPI(`/engineering/review-context/${maintenanceRequestId}`);
}

export async function executeEngineeringDecision(payload: {
  maintenance_request_id: string;
  engineer_id: string;
  decision: string;
  instruction_code: string;
  technical_directive: string;
  required_repair_procedure: string;
  authorized_engineer: string;
  decision_date: string;
  required_tools?: string | null;
  required_parts?: string | null;
  safety_notes?: string | null;
}) {
  return fetchAPI("/engineering/technical-decision", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function startRepair(maintenanceRequestId: string, assignedSectionId: string, assignedTechnicianId: string, instructionId: string, toolId?: string) {
  return fetchAPI("/technical-section/start-repair", {
    method: "POST",
    body: JSON.stringify({
      maintenance_request_id: maintenanceRequestId,
      assigned_section_id: assignedSectionId,
      assigned_technician_id: assignedTechnicianId,
      instruction_id: instructionId,
      tool_id: toolId || null,
    }),
  });
}

export async function getTools() {
  return fetchAPI("/tools");
}

export async function registerWorkLog(payload: {
  maintenance_request_id: string;
  repair_task_id: string;
  performed_by: string;
  task_description: string;
  man_hours: number;
  replaced_parts: string;
  consumables_used: string;
  technical_observations: string;
}) {
  return fetchAPI("/technical-section/work-log", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getWorkLogs(maintenanceRequestId: string) {
  return fetchAPI(`/technical-section/work-logs/${maintenanceRequestId}`);
}

export async function completeRepair(payload: {
  maintenance_request_id: string;
  repair_task_id: string;
  performed_by: string;
  repair_completion_record_code: string;
  notes: string;
}) {
  return fetchAPI("/technical-section/complete-repair", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function approveRepair(repairTaskId: string, inspectorId: string, isCritical: boolean = false, secondInspectorId?: string) {
  return fetchAPI("/quality/approve-repair", {
    method: "POST",
    body: JSON.stringify({
      repair_task_id: repairTaskId,
      inspector_id: inspectorId,
      is_critical: isCritical,
      second_inspector_id: secondInspectorId || null,
    }),
  });
}

export async function releaseComponent(
  componentId: string,
  maintenanceRequestId: string,
  qualityInspectionId: string,
  releasedBy: string,
  returnedToDepartmentId: string,
  serviceReleaseCertificateCode: string,
  historicalRecordBookCode: string
) {
  return fetchAPI("/arsenal/release-component", {
    method: "POST",
    body: JSON.stringify({
      component_id: componentId,
      maintenance_request_id: maintenanceRequestId,
      quality_inspection_id: qualityInspectionId,
      released_by: releasedBy,
      returned_to_department_id: returnedToDepartmentId,
      service_release_certificate_code: serviceReleaseCertificateCode,
      historical_record_book_code: historicalRecordBookCode,
    }),
  });
}

export async function installComponent(aircraftId: string, componentId: string, positionCode: string, installedBy: string) {
  return fetchAPI("/squadron/install-component", {
    method: "POST",
    body: JSON.stringify({
      aircraft_id: aircraftId,
      component_id: componentId,
      position_code: positionCode,
      installed_by: installedBy,
    }),
  });
}
