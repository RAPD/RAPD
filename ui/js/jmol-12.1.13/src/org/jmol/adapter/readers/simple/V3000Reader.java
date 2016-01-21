/* $RCSfile$
 * $Author: hansonr $
 * $Date: 2006-03-15 08:52:29 -0500 (Wed, 15 Mar 2006) $
 * $Revision: 4614 $
 *
 * Copyright (C) 2006  Miguel, Jmol Development, www.jmol.org
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

package org.jmol.adapter.readers.simple;

import org.jmol.adapter.smarter.*;
import org.jmol.api.JmolAdapter;

/**
 * A reader for MDL V3000 files
 *<p>
 * <a href='http://www.mdli.com/downloads/public/ctfile/ctfile.jsp'>
 * http://www.mdli.com/downloads/public/ctfile/ctfile.jsp
 * </a>
 *<p>
 */
public class V3000Reader extends AtomSetCollectionReader {
    
  private int headerAtomCount;
  private int headerBondCount;

  @Override
  protected boolean checkLine() throws Exception {
    if (!doGetModel(++modelNumber)) {
      discardLinesUntilContains("$$$$");
      return checkLastModel();
    }
    processCtab();
    return true;
  }

  private void processCtab() throws Exception {
    while (readLine() != null &&
           ! line.startsWith("$$$$") &&
           ! line.startsWith("M  END")) {
      if (line.startsWith("M  V30 BEGIN ATOM")) {
        processAtomBlock();
        continue;
      }
      if (line.startsWith("M  V30 BEGIN BOND")) {
        processBondBlock();
        continue;
      }
      if (line.startsWith("M  V30 BEGIN CTAB")) {
        newAtomSet("");
      } else if (line.startsWith("M  V30 COUNTS")) {
        headerAtomCount = parseInt(line, 13);
        headerBondCount = parseInt();
      }
    }
    if (line != null && !line.startsWith("$$$$"))
      discardLinesUntilStartsWith("$$$$");
  }

  private String processAtomBlock() throws Exception {
    for (int i = headerAtomCount; --i >= 0; ) {
      readLineWithContinuation();
      if (line == null || (! line.startsWith("M  V30 ")))
        throw new Exception("unrecognized atom");
      Atom atom = new Atom();
      String[] tokens = getTokens();
      atom.atomSerial = parseInt(tokens[2]);
      atom.elementSymbol = tokens[3];
      atom.set(parseFloat(tokens[4]), parseFloat(tokens[5]), parseFloat(tokens[6]));
      for (int j = 8; j < tokens.length; j++) {
        String token = tokens[j];
        if (token.startsWith("CHG=")) {
          int charge = parseInt(token, 4);
          atom.formalCharge = (charge > 3 ? 4 - charge : charge);
          break;
        } else if (token.startsWith("MASS=")) {
          int isotope = parseInt(token, 5);
          atom.elementNumber = (short) ((isotope << 7) + JmolAdapter
              .getElementNumber(atom.elementSymbol));
        }
      }
      atomSetCollection.addAtomWithMappedSerialNumber(atom);
    }
    readLine();
    if (line == null || ! line.startsWith("M  V30 END ATOM"))
      throw new Exception("M  V30 END ATOM not found");
    return line;
  }

  private void processBondBlock() throws Exception {
    for (int i = headerBondCount; --i >= 0; ) {
      readLineWithContinuation();
      if (line == null || (! line.startsWith("M  V30 ")))
        throw new Exception("unrecognized bond");
      /*int bondSerial = */parseInt(line, 7); // currently unused
      int order = parseInt();
      int atomSerial1 = parseInt();
      int atomSerial2 = parseInt();
      atomSetCollection.addNewBondWithMappedSerialNumbers(atomSerial1,
                                                          atomSerial2,
                                                          order);
    }
    readLine();
    if (line == null || ! line.startsWith("M  V30 END BOND"))
      throw new Exception("M  V30 END BOND not found");
  }

  private void readLineWithContinuation() throws Exception {
    readLine();
    if (line != null && line.length() > 7) {
      while (line.charAt(line.length() - 1) == '-') {
        String line2 = readLine();
        if (line2 == null || ! line.startsWith("M  V30 "))
          throw new Exception("Invalid line continuation");
        line += line2.substring(7);
      }
    }
  }
  
}
