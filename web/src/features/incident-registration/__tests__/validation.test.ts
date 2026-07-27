import { describe, expect, it } from "vitest";
import {
  incidentFormSchema,
  defaultIncidentFormValues,
} from "../validation/incidentForm.schema";

const VALID_UUID = "11111111-1111-1111-1111-111111111111";

describe("incidentFormSchema", () => {
  it("accepts a valid form", () => {
    const res = incidentFormSchema.safeParse({
      ...defaultIncidentFormValues,
      incidentTypeId: VALID_UUID,
      reporterContact: "+7 900 123-45-67",
    });
    expect(res.success).toBe(true);
  });

  it("requires a valid incident type id", () => {
    const res = incidentFormSchema.safeParse({
      ...defaultIncidentFormValues,
      incidentTypeId: "",
    });
    expect(res.success).toBe(false);
  });

  it("rejects an invalid phone", () => {
    const res = incidentFormSchema.safeParse({
      ...defaultIncidentFormValues,
      incidentTypeId: VALID_UUID,
      reporterContact: "abc",
    });
    expect(res.success).toBe(false);
  });

  it("allows empty optional fields", () => {
    const res = incidentFormSchema.safeParse({
      ...defaultIncidentFormValues,
      incidentTypeId: VALID_UUID,
      reporterName: "",
      reporterContact: "",
      description: "",
    });
    expect(res.success).toBe(true);
  });
});
