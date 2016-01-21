/* $RCSfile$
 * $Author: hansonr $
 * $Date: 2010-08-06 06:11:49 +0200 (ven., 06 août 2010) $
 * $Revision: 13843 $

 *
 * Copyright (C) 2003-2005  Miguel, Jmol Development, www.jmol.org
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
package org.jmol.viewer;

import java.util.BitSet;

import org.jmol.modelset.ModelLoader;
import org.jmol.modelset.ModelSet;

class ModelManager {

  private final Viewer viewer;
  private ModelLoader modelLoader;

  private String fullPathName;
  private String fileName;

  ModelManager(Viewer viewer) {
    this.viewer = viewer;
  }

  ModelSet zap() {
    fullPathName = fileName = null;
    modelLoader = new ModelLoader(viewer, viewer.getZapName());
    return modelLoader;
  }
  
  String getModelSetFileName() {
    return (fileName != null ? fileName : viewer.getZapName());
  }

  String getModelSetPathName() {
    return fullPathName;
  }

  ModelSet createModelSet(String fullPathName, String fileName,
                          StringBuffer loadScript, Object atomSetCollection, BitSet bsNew, boolean isAppend) {
    // 11.9.10 11/22/2009 bh adjusted to never allow a null return
    if (isAppend) {
      if (atomSetCollection != null) {
        String name = modelLoader.getModelSetName();
        if (name.indexOf(" (modified)") < 0)
          name += " (modified)";
        modelLoader = new ModelLoader(viewer, loadScript, atomSetCollection,
            modelLoader, name, bsNew);
      }
    } else if (atomSetCollection == null) {
      return zap();
    } else {
      this.fullPathName = fullPathName;
      this.fileName = fileName;
      String modelSetName = viewer.getModelAdapter().getAtomSetCollectionName(
          atomSetCollection);
      if (modelSetName != null) {
        modelSetName = modelSetName.trim();
        if (modelSetName.length() == 0)
          modelSetName = null;
      }
      if (modelSetName == null)
        modelSetName = reduceFilename(fileName);
      modelLoader = new ModelLoader(viewer, loadScript, atomSetCollection,
          null, modelSetName, bsNew);
    }
    if (modelLoader.getAtomCount() == 0)
      zap();
    return modelLoader;
  }

  private static String reduceFilename(String fileName) {
    if (fileName == null)
      return null;
    int ichDot = fileName.indexOf('.');
    if (ichDot > 0)
      fileName = fileName.substring(0, ichDot);
    if (fileName.length() > 24)
      fileName = fileName.substring(0, 20) + " ...";
    return fileName;
  }

}
