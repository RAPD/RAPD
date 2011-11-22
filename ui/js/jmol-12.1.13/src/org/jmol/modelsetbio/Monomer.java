/* $RCSfile$
 * $Author: hansonr $
 * $Date: 2007-02-15 11:45:59 -0600 (Thu, 15 Feb 2007) $
 * $Revision: 6834 $
 *
 * Copyright (C) 2004-2005  The Jmol Development Team
 *
 * Contact: jmol-developers@lists.sf.net
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *  Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
 */
package org.jmol.modelsetbio;


import org.jmol.modelset.Atom;
import org.jmol.modelset.Bond;
import org.jmol.modelset.Chain;
import org.jmol.modelset.Group;

import org.jmol.util.Logger;
import org.jmol.util.Measure;
import org.jmol.util.Quaternion;
import org.jmol.viewer.JmolConstants;
import org.jmol.script.Token;

import java.util.Hashtable;
import java.util.BitSet;
import java.util.List;
import java.util.Map;

import javax.vecmath.Point3f;

public abstract class Monomer extends Group {

  BioPolymer bioPolymer;

  protected final byte[] offsets;

  protected Monomer(Chain chain, String group3, int seqcode,
          int firstAtomIndex, int lastAtomIndex,
          byte[] interestingAtomOffsets) {
    super(chain, group3, seqcode, firstAtomIndex, lastAtomIndex);
    offsets = interestingAtomOffsets;
    leadAtomIndex = firstAtomIndex + (offsets[0] & 0xFF);
  }

  int monomerIndex;
  int leadAtomIndex;
  
  void setBioPolymer(BioPolymer polymer, int index) {
    this.bioPolymer = polymer;
    monomerIndex = index;
  }

  @Override
  public int getSelectedMonomerCount() {
    return bioPolymer.getSelectedMonomerCount();
  }
  
  @Override
  public int getSelectedMonomerIndex() {
    return (monomerIndex >= 0 && bioPolymer.isMonomerSelected(monomerIndex) ? monomerIndex : -1);
  }
  
  public BioPolymer getBioPolymer() {
    return bioPolymer;
  }
  
  @Override
  public int getBioPolymerLength() {
    return bioPolymer == null ? 0 : bioPolymer.monomerCount;
  }

  @Override
  public int getMonomerIndex() {
    return monomerIndex;
  }

  @Override
  public int getBioPolymerIndexInModel() {
    return (bioPolymer == null ? -1 : bioPolymer.bioPolymerIndexInModel);
  }
  

  ////////////////////////////////////////////////////////////////

  protected static byte[] scanForOffsets(int firstAtomIndex,
                               int[] specialAtomIndexes,
                               byte[] interestingAtomIDs) {
    /*
     * from validateAndAllocate in AminoMonomer or NucleicMonomer extensions
     * 
     * sets offsets for the FIRST conformation ONLY
     * (provided that the conformation is listed first in each atom case)
     *  
     *  specialAtomIndexes[] corrolates with JmolConstants.specialAtomNames[]
     *  and is set up back in the calling frame.distinguishAndPropagateGroups
     */
    int interestingCount = interestingAtomIDs.length;
    byte[] offsets = new byte[interestingCount];
    for (int i = interestingCount; --i >= 0; ) {
      int atomIndex;
      int atomID = interestingAtomIDs[i];
      // mth 2004 06 09
      // use ~ instead of - as the optional indicator
      // because I got hosed by a missing comma
      // in an interestingAtomIDs table
      if (atomID < 0) {
        atomIndex = specialAtomIndexes[~atomID]; // optional
      } else {
        atomIndex = specialAtomIndexes[atomID];  // required
        if (atomIndex < 0)
          return null;
      }
      int offset;
      if (atomIndex < 0)
        offset = 255;
      else {
        offset = atomIndex - firstAtomIndex;
        if (offset < 0 || offset > 254) {
          Logger.warn("Monomer.scanForOffsets i="+i+" atomID="+atomID+" atomIndex:"+atomIndex+" firstAtomIndex:"+firstAtomIndex+" offset out of 0-254 range. Groups aren't organized correctly. Is this really a protein?: "+offset);
          if (atomID < 0) {
            offset = 255; //it was optional anyway RMH
          } else {
            //throw new NullPointerException();
          }
        }
      }
      offsets[i] = (byte)offset;
    }
    return offsets;
  }

  ////////////////////////////////////////////////////////////////

  @Override
  public boolean isDna() { return false; }
  @Override
  public boolean isRna() { return false; }
  @Override
  public boolean isProtein() {
    return isAmino;
  }
  @Override
  public final boolean isNucleic() {return this instanceof PhosphorusMonomer;}

  ////////////////////////////////////////////////////////////////

  /**
   * @param proteinstructure 
   * 
   */
  void setStructure(ProteinStructure proteinstructure) { }

  public ProteinStructure getProteinStructure() { return null; }
  @Override
  public byte getProteinStructureType() { return JmolConstants.PROTEIN_STRUCTURE_NONE; }
  public boolean isHelix() { return false; }
  public boolean isSheet() { return false; }
  @Override
  public void setProteinStructureId(int id) { }

  ////////////////////////////////////////////////////////////////
/*
  public final Atom getAtomFromOffset(byte offset) {
    if (offset == -1)
      return null;
    return chain.frame.atoms[firstAtomIndex + (offset & 0xFF)];
  }

  public final Point3f getAtomPointFromOffset(byte offset) {
    if (offset == -1)
      return null;
    return chain.frame.atoms[firstAtomIndex + (offset & 0xFF)];
  }
*/
  
  ////////////////////////////////////////////////////////////////

  protected final Atom getAtomFromOffsetIndex(int offsetIndex) {
    if (offsetIndex > offsets.length)
      return null;
    int offset = offsets[offsetIndex] & 0xFF;
    if (offset == 255)
      return null;
    return chain.getAtom(firstAtomIndex + offset);
  }

  protected final Atom getSpecialAtom(byte[] interestingIDs, byte specialAtomID) {
    for (int i = interestingIDs.length; --i >= 0; ) {
      int interestingID = interestingIDs[i];
      if (interestingID < 0)
        interestingID = -interestingID;
      if (specialAtomID == interestingID) {
        int offset = offsets[i] & 0xFF;
        if (offset == 255)
          return null;
        return chain.getAtom(firstAtomIndex + offset);
      }
    }
    return null;
  }

  protected final Point3f getSpecialAtomPoint(byte[] interestingIDs,
                                    byte specialAtomID) {
    for (int i = interestingIDs.length; --i >= 0; ) {
      int interestingID = interestingIDs[i];
      if (interestingID < 0)
        interestingID = -interestingID;
      if (specialAtomID == interestingID) {
        int offset = offsets[i] & 0xFF;
        if (offset == 255)
          return null;
        return chain.getAtom(firstAtomIndex + offset);
      }
    }
    return null;
  }
/*
  public Atom getAtom(byte specialAtomID) { return null; }

  protected Point3f getAtomPoint(byte specialAtomID) { return null; }
*/
  
  @Override
  public boolean isLeadAtom(int atomIndex) {
    return atomIndex == leadAtomIndex;
  }

  @Override
  public final Atom getLeadAtom() {
    return getAtomFromOffsetIndex(0);
  }

  @Override
  public int getLeadAtomIndex() {
    return getLeadAtom().index;
  }

  public final Atom getWingAtom() {
    return getAtomFromOffsetIndex(1);
  }

  Atom getInitiatorAtom() {
    return getLeadAtom();
  }
  
  Atom getTerminatorAtom() {
    return getLeadAtom();
  }

  abstract boolean isConnectedAfter(Monomer possiblyPreviousMonomer);

  /**
   * Selects LeadAtom when this Monomer is clicked iff it is
   * closer to the user.
   * 
   * @param x
   * @param y
   * @param closest
   * @param madBegin
   * @param madEnd
   */
  void findNearestAtomIndex(int x, int y, Atom[] closest,
                            short madBegin, short madEnd) {
  }

  @Override
  protected boolean calcBioParameters() {
    return bioPolymer.calcParameters();
  }

  @Override
  public boolean haveParameters() {
    return bioPolymer.haveParameters;
  }
  
  public Map<String, Object> getMyInfo() {
    Map<String, Object> info = new Hashtable<String, Object>();
    char chainID = chain.getChainID();
    info.put("chain", (chainID == '\0' ? "" : "" + chainID));
    int seqNum = getSeqNumber();
    char insCode = getInsertionCode();
    if (seqNum > 0)      
      info.put("sequenceNumber", Integer.valueOf(seqNum));
    if (insCode != 0)      
      info.put("insertionCode","" + insCode);
    info.put("atomInfo1", chain.getAtom(firstAtomIndex).getInfo());
    info.put("atomInfo2", chain.getAtom(lastAtomIndex).getInfo());
    info.put("_apt1", Integer.valueOf(firstAtomIndex));
    info.put("_apt2", Integer.valueOf(lastAtomIndex));
    info.put("atomIndex1", Integer.valueOf(firstAtomIndex));
    info.put("atomIndex2", Integer.valueOf(lastAtomIndex));
    float f = getGroupParameter(Token.phi);
    if (!Float.isNaN(f))
      info.put("phi", new Float(f));
    f = getGroupParameter(Token.psi);
    if (!Float.isNaN(f))
      info.put("psi", new Float(f));
    f = getGroupParameter(Token.eta);
    if (!Float.isNaN(f))
      info.put("mu", new Float(f));
    f = getGroupParameter(Token.theta);
    if (!Float.isNaN(f))
      info.put("theta", new Float(f));
    ProteinStructure structure = getProteinStructure();
    if(structure != null) {
      info.put("structureId", Integer.valueOf(structure.uniqueID));
      info.put("structureType", JmolConstants.getProteinStructureName(structure.type, false));
    }
    info.put("shapeVisibilityFlags", Integer.valueOf(shapeVisibilityFlags));
    return info;
  }
  
  @Override
  public String getStructureId() {
    ProteinStructure structure = getProteinStructure();
    return (structure == null ? "" : JmolConstants.getProteinStructureName(structure.type, false));
  }
  
  final void updateOffsetsForAlternativeLocations(BitSet bsSelected,
                                                  int nAltLocInModel) {
    chain.updateOffsetsForAlternativeLocations(bsSelected, nAltLocInModel,
        offsets, firstAtomIndex, lastAtomIndex);
  }
    
  final void getMonomerSequenceAtoms(BitSet bsInclude, BitSet bsResult) {
    for (int j = firstAtomIndex; j <= lastAtomIndex; j++)
      if (bsInclude.get(j))
        bsResult.set(j);
  }
  
  protected final static boolean checkOptional(byte[]offsets, byte atom, 
                                               int firstAtomIndex, 
                                               int index) {
    if (offsets[atom] >= 0)
      return true;
    if (index < 0)
      return false;
    offsets[atom] = (byte)(index - firstAtomIndex);
    return true;
  }

  /**
   * 
   * @param qtype
   * @return center
   */
  Point3f getQuaternionFrameCenter(char qtype) {
    return null; 
  }

  protected Object getHelixData2(int tokType, char qType, int mStep) {
    int iPrev = monomerIndex - mStep;
    Monomer prev = (mStep < 1 || monomerIndex <= 0 ? null : bioPolymer.monomers[iPrev]);
    Quaternion q2 = getQuaternion(qType);
    Quaternion q1 = (mStep < 1 ? Quaternion.getQuaternionFrame(JmolConstants.axisX, JmolConstants.axisY, JmolConstants.axisZ, false) 
        : prev == null ? null : prev.getQuaternion(qType));
    if (q1 == null || q2 == null)
      return super.getHelixData(tokType, qType, mStep);
    Point3f a = (mStep < 1 ? new Point3f(0, 0, 0) : prev.getQuaternionFrameCenter(qType));
    Point3f b = getQuaternionFrameCenter(qType);
    if (a == null || b == null)
      return super.getHelixData(tokType, qType, mStep);
    return Measure.computeHelicalAxis(tokType == Token.draw ? "helixaxis" + getUniqueID() : null, 
        tokType, a, b, q2.div(q1));
  }

  public String getUniqueID() {
    char cid = getChainID();
    Atom a = getLeadAtom();
    String id = (a == null ? "" : "_" + a.getModelIndex()) + "_" + getResno()
        + (cid == '\0' ? "" : "" + cid);
    cid = (a == null ? '\0' : getLeadAtom().getAlternateLocationID());
    if (cid != '\0')
      id += cid;
    return id;
  }
  
  @Override
  public boolean isCrossLinked(Group g) {
    for (int i = firstAtomIndex; i <= lastAtomIndex; i++)
      if (getCrossLink(i, null, g))
          return true;
    return false;
  }
 
  @Override
  public boolean getCrossLinkLeadAtomIndexes(List<Integer> vReturn) {    
   for (int i = firstAtomIndex; i <= lastAtomIndex; i++)
      if (getCrossLink(i, vReturn) && vReturn == null)
          return true;
    return false;
  }  

  protected boolean getCrossLink(int i, List<Integer> vReturn) {
    return getCrossLink(i, vReturn, null);
  }
  
  private boolean getCrossLink(int i, List<Integer> vReturn, Group group) {
    // vReturn null --> just checking for connection to previous group
    // not obvious from PDB file for carbohydrates
    Atom atom = chain.getAtom(i);
    Bond[] bonds = atom.getBonds();
    int ibp = getBioPolymerIndexInModel();
    if (ibp < 0 || bonds == null)
      return false;
    boolean haveCrossLink = false;
    boolean checkPrevious = (vReturn == null && group == null);
    for (int j = 0; j < bonds.length; j++) {
      Atom a = bonds[j].getOtherAtom(atom);
      Group g = a.getGroup();
      if (group != null && g != group)
        continue;
      int iPolymer = g.getBioPolymerIndexInModel();
      int igroup = g.getMonomerIndex();
      if (checkPrevious) {
        if (iPolymer == ibp && igroup == monomerIndex - 1)
          return true;
      } else if (iPolymer >= 0
          && igroup >= 0
          && (iPolymer != ibp || igroup < monomerIndex - 1 || igroup > monomerIndex + 1)) {
        haveCrossLink = true;
        if (group != null)
          break;
        vReturn.add(Integer.valueOf(g.getLeadAtomIndex()));
      }
    }
    return haveCrossLink;
  }
  
  @Override
  public boolean isConnectedPrevious() {
    return true; // but not nec. for carbohydrates... see 1k7c
  }

}
  

