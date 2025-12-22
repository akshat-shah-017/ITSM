# ITSM Filter/Sort Fix - Implementation Plan

## Issues Found

1. **Sorting parameter mismatch**: Frontend sends `sort`, backend's `OrderingFilter` expects `ordering`
2. **Status filter case sensitivity**: Backend might be using uppercase (NEW, ASSIGNED) vs frontend lowercase (New, Assigned)

## Fix Plan

### 1. Create custom OrderingFilter using 'sort' parameter
Create a custom filter in `core/filters.py` that uses `sort` as the parameter name.

### 2. Update all views to use custom filter
Apply to: TicketListView, EmployeeQueueView, EmployeeTicketsView, ManagerTeamTicketsView

### 3. Verify status filter compatibility
Test if status values in FilterBar match backend TicketStatus.CHOICES
