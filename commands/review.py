"""Merge-request review workflow."""

from legacy import (
    openMergeRequestInBrowser,
    getActiveMergeRequestId,
    find_merge_request_id_by_branch,
    addReviewersToMergeRequest,
    setMergeRequestToAutoMerge,
    getCurrentIssueId,
    track_issue_time,
)
